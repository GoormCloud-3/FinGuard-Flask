import os
import boto3
import sagemaker

from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.step_collections import RegisterModel
from sagemaker.workflow.lambda_step import LambdaStep, LambdaOutput, LambdaOutputTypeEnum
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.functions import JsonGet
from sagemaker.workflow.conditions import ConditionGreaterThan
from sagemaker.processing import ScriptProcessor, ProcessingInput, ProcessingOutput
from sagemaker.inputs import TrainingInput
from sagemaker.estimator import Estimator
from sagemaker.model import Model
from sagemaker.model_metrics import ModelMetrics, MetricsSource
from sagemaker.lambda_helper import Lambda
from sagemaker.workflow.properties import PropertyFile

# execution role
role = os.environ["SAGEMAKER_JOB_ROLE"]

# settings
region = boto3.Session().region_name
bucket = "finguard-model-artifacts"
session = PipelineSession(default_bucket=bucket)
prefix = "data"
input_data = f"s3://{bucket}/{prefix}/finguard_transdata.csv"

# scikit-learn image for XGBoost
sklearn_image = sagemaker.image_uris.retrieve(
   framework="sklearn",
   region=region,
   version="1.0-1",
   py_version="py3"
)
# Step 1: PreProcessing
script_processor = ScriptProcessor(
    image_uri=sklearn_image,
    role=role,
    instance_count=1,
    instance_type="ml.m5.large",
    command=["python3"],
    sagemaker_session = session
)

step_process = ProcessingStep(
    name="PreprocessStep",
    processor=script_processor,
    inputs=[ProcessingInput(source=input_data, destination="/opt/ml/processing/input")],
    outputs=[
        ProcessingOutput(output_name="train", source="/opt/ml/processing/train"),
        ProcessingOutput(output_name="test", source="/opt/ml/processing/test")
    ],
    code="preprocessing.py"
)

# Step 2: Training with XGBoost (built-in)
xgb_image = sagemaker.image_uris.retrieve(
        "xgboost", 
        region=region, 
        version="1.5-1"
        )
xgb_estimator = Estimator(
    image_uri=xgb_image,
    instance_type="ml.m5.large",
    instance_count=1,
    role=role,
    output_path=f"s3://{bucket}/model",
    hyperparameters={
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "num_round": 100
    },
    sagemaker_session = session
)

step_train = TrainingStep(
    name="XGBoostTrainStep",
    estimator=xgb_estimator,
    inputs={
        "train": TrainingInput(
            s3_data=step_process.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri,
            content_type="text/csv"
        )
    }
)

# Step 3: Evaluation
evaluation_report = PropertyFile(
    name="EvaluationReport",
    output_name="evaluation",
    path="evaluation.json",
)

eval_processor = ScriptProcessor(
    image_uri=xgb_image,
    role=role,
    instance_type="ml.m5.large",
    instance_count=1,
    command=["python3"],
    sagemaker_session=session
    )

step_eval = ProcessingStep(
    name="EvaluateStep",
    processor=eval_processor,
    inputs=[
        ProcessingInput(
            source=step_train.properties.ModelArtifacts.S3ModelArtifacts,
            destination="/opt/ml/processing/model"
        ),
        ProcessingInput(
            source=step_process.properties.ProcessingOutputConfig.Outputs["test"].S3Output.S3Uri,
            destination="/opt/ml/processing/test"
        )
    ],
    outputs=[ProcessingOutput(output_name="evaluation", source="/opt/ml/processing/evaluation")],
    code="evaluation.py",
    property_files=[evaluation_report]
)

# Step 4: Register + Deploy (AUC >= 기존 AUC)
# set metric path of eval result
model_metrics = ModelMetrics(
    model_statistics=MetricsSource(
        s3_uri=step_eval.properties.ProcessingOutputConfig.Outputs["evaluation"].S3Output.S3Uri,
        content_type="application/json"
    )
)

# create model object
INFERENCE_IMAGE_URI = os.environ.get("INFERENCE_IMAGE_URI")
model = Model(
    image_uri=INFERENCE_IMAGE_URI,
    model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
    sagemaker_session=session,
    role=role
)

# save model
step_register = RegisterModel(
    name="RegisterXGBModel",
    model=model,
    content_types=["text/csv"],
    response_types=["text/csv"],
    model_package_group_name="FraudDetectionXGBGroup",
    approval_status="Approved",
    model_metrics=model_metrics
)

# get previous auc
lambda_func = Lambda(
    function_arn=os.environ["GET_PREV_AUC_LAMBDA_ARN"],
    session=session
)

step_lambda = LambdaStep(
    name="GetPreviousModelAUC",
    lambda_func=lambda_func,
    outputs=[
        LambdaOutput(output_name="previous_auc", output_type=LambdaOutputTypeEnum.Float)
    ]
)

# compare auc
step_cond = ConditionStep(
    name="CheckAUC",
    conditions=[
        ConditionGreaterThan(
            left=JsonGet(
                step_name=step_eval.name,
                property_file=evaluation_report,
                json_path="metrics.auc"
            ),
            right=step_lambda.properties.Outputs["previous_auc"]
        )
    ],
    if_steps=[step_register],
    else_steps=[]
)

# Set pipeline
pipeline = Pipeline(
    name="FraudDetectionXGBPipeline",
    steps=[step_process, step_train, step_eval, step_lambda, step_cond],
    sagemaker_session=session,
)
