# Partial S3 backend: the bucket and key are supplied at init time with
#   terraform init -backend-config=backend.hcl
# (copy backend.hcl.example to backend.hcl, which is gitignored). CI and the local checks use `init -backend=false`.
terraform {
  backend "s3" {}
}
