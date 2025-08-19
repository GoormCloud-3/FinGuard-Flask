from pipeline import pipeline
import json

# take Pipeline JSON set
definition = pipeline.definition()

# 저장
with open("Infra/pipeline_definition.json", "w") as f:
    f.write(definition)

print("pipeline_definition.json has been exported to Infra/")

