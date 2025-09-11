terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"    # 5.6x대 권장 (팀 표준에 맞게 조정 가능)
    }
  }
}
