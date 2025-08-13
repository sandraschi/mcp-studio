# CI/CD Setup Guide

This document explains how to set up and use the GitHub Actions workflows for continuous integration and deployment of the MCP Studio application.

## Prerequisites

1. A GitHub repository for the project
2. Required secrets configured in GitHub (see below)
3. Docker Hub account (for container registry)
4. AWS account (for S3/CloudFront deployment)

## GitHub Secrets

You'll need to configure the following secrets in your GitHub repository settings (Settings > Secrets and variables > Actions):

### Backend Secrets
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Your Docker Hub access token
- `STAGING_HOST`: Staging server hostname or IP
- `STAGING_USERNAME`: SSH username for staging
- `STAGING_SSH_KEY`: Private SSH key for staging
- `PROD_HOST`: Production server hostname or IP
- `PROD_USERNAME`: SSH username for production
- `PROD_SSK_KEY`: Private SSH key for production

### Frontend Secrets
- `AWS_ACCESS_KEY_ID`: AWS access key with S3 and CloudFront permissions
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key
- `AWS_S3_BUCKET_STAGING`: S3 bucket name for staging
- `AWS_S3_BUCKET_PRODUCTION`: S3 bucket name for production
- `CLOUDFRONT_DISTRIBUTION_ID_STAGING`: CloudFront distribution ID for staging
- `CLOUDFRONT_DISTRIBUTION_ID_PRODUCTION`: CloudFront distribution ID for production
- `REACT_APP_STAGING_API_URL`: API URL for staging environment
- `REACT_APP_PRODUCTION_API_URL`: API URL for production environment

## Workflows

### Backend CI/CD

**File:** `.github/workflows/backend-ci-cd.yml`

This workflow handles:
1. Running tests on multiple Python versions and operating systems
2. Building and pushing Docker images to Docker Hub
3. Deploying to staging/production environments

**Triggered on:**
- Push to `main` or `develop` branches (backend changes only)
- Pull requests to `main` or `develop` (backend changes only)

### Frontend CI/CD

**File:** `.github/workflows/frontend-ci-cd.yml`

This workflow handles:
1. Running tests and building the React application
2. Deploying to S3/CloudFront (staging/production)
3. Building and pushing Docker images to Docker Hub

**Triggered on:**
- Push to `main` or `develop` branches (frontend changes only)
- Pull requests to `main` or `develop` (frontend changes only)

## Deployment Environments

### Staging
- **Branch:** `develop`
- **Deployment:** Automatic on push to `develop`
- **URL:** Configured in `REACT_APP_STAGING_API_URL`

### Production
- **Branch:** `main`
- **Deployment:** Manual (requires approval)
- **URL:** Configured in `REACT_APP_PRODUCTION_API_URL`

## Manual Deployment

To manually trigger a deployment:

1. Go to the "Actions" tab in your GitHub repository
2. Select the workflow you want to run
3. Click "Run workflow"
4. Select the branch and click "Run workflow"

## Monitoring

- **GitHub Actions:** View workflow runs in the "Actions" tab
- **Docker Hub:** Check built images in your Docker Hub repository
- **AWS:** Monitor deployments in the AWS Console (CloudFront, S3, etc.)

## Troubleshooting

### Common Issues

1. **Workflow not triggering**
   - Check the `on` section in the workflow file
   - Ensure the changed files match the specified paths

2. **Docker build/push failures**
   - Verify Docker Hub credentials
   - Check Dockerfile for errors

3. **Deployment failures**
   - Check SSH keys and permissions
   - Verify server configurations

4. **Test failures**
   - Run tests locally to reproduce issues
   - Check test logs in the workflow run

## Best Practices

1. Always create feature branches from `develop`
2. Open pull requests for code review
3. Run tests locally before pushing
4. Monitor workflow runs after pushing changes
5. Keep sensitive information in GitHub Secrets
6. Use environment variables for configuration
