# GCP Services Usage Log

**Project**: `ttb-lang1`
**Account**: `chillcoders@gmail.com`
**Date**: 2025-02-04
**Total Enabled Services**: 38

---

## 🚀 Compute & Deployment Services

### Cloud Run Admin API (`run.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Deploy containerized Next.js and Python applications
- **MCP Integration**: Cloud Run MCP Server uses this API
- **Usage**: Primary deployment target for the MCP Finance application
- **Related**: Works with Artifact Registry for image storage

### Cloud Build API (`cloudbuild.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Automated CI/CD pipeline for building containers
- **Usage**: Can be used for automated builds from source repositories
- **Integration**: Builds Docker images for Cloud Run deployments

### Cloud Functions API (`cloudfunctions.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Serverless compute for functions (lightweight alternative to Cloud Run)
- **Usage**: Could be used for background jobs or event-driven processing
- **Note**: Currently focused on Cloud Run, but available if needed

---

## 💾 Data & Storage Services

### Cloud Storage API (`storage.googleapis.com`, `storage-api.googleapis.com`, `storage-component.googleapis.com`)
- **Status**: ✅ Enabled (3 related APIs)
- **Purpose**: Object storage for files, backups, and data
- **Usage**: Can store backups, logs, or file uploads for MCP Finance
- **Integration**: Works with Cloud Build for artifact storage

### Cloud Firestore API (`firestore.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: NoSQL document database
- **Usage**: Real-time database for user sessions, trading data
- **Alternative**: PostgreSQL with Drizzle ORM is primary (see project guidelines)

### Cloud Datastore API (`datastore.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Legacy NoSQL database (predecessor to Firestore)
- **Usage**: Not recommended for new features; Firestore is preferred
- **Note**: Kept for backward compatibility if needed

### Cloud SQL (`sql-component.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Managed relational database service
- **Usage**: Could host PostgreSQL instances (though currently using local/external PostgreSQL)
- **Consideration**: May be useful for production database hosting

---

## 📊 BigQuery & Data Warehouse Services

### BigQuery API (`bigquery.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Data warehouse and analytics platform
- **Usage**: Could analyze trading data, user behavior, market trends
- **Potential**: Historical market data analysis and reporting

### BigQuery Connection API (`bigqueryconnection.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Connect BigQuery to external data sources
- **Usage**: Integrate with external market data APIs

### BigQuery Data Transfer API (`bigquerydatatransfer.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Automated data pipeline scheduling
- **Usage**: Regular imports of market data or user analytics

### BigQuery Data Policy API (`bigquerydatapolicy.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Data governance and access control
- **Usage**: Protect sensitive trading and financial data

### BigQuery Migration API (`bigquerymigration.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Migrate SQL from other databases to BigQuery
- **Usage**: If planning to migrate data warehouses

### BigQuery Reservation API (`bigqueryreservation.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Manage BigQuery compute resources
- **Usage**: Reserve compute capacity for consistent performance

### BigQuery Storage API (`bigquerystorage.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: High-performance data reading from BigQuery
- **Usage**: Faster analysis of large financial datasets

---

## 🤖 AI & Machine Learning Services

### Vertex AI API (`aiplatform.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Google's unified ML platform
- **Potential Uses**:
  - Stock price prediction models
  - Sentiment analysis for market trends
  - Automated trading signal generation
  - Risk assessment models
- **Note**: Could enhance stock analysis features in MCP Finance

---

## 📦 Container & Artifact Services

### Artifact Registry API (`artifactregistry.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Store and manage Docker images
- **Usage**: Primary container image repository for Cloud Run
- **Integration**: Cloud Build pushes images here; Cloud Run pulls from here

### Container Registry API (`containerregistry.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Legacy container image storage
- **Usage**: Alternative to Artifact Registry (older service)
- **Note**: Artifact Registry is the modern replacement

---

## 📊 Monitoring & Logging Services

### Cloud Logging API (`logging.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Centralized logging for all applications
- **Usage**: Track errors, debug issues in production
- **Integration**: Cloud Run applications automatically log here

### Cloud Monitoring API (`monitoring.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Metrics and alerting
- **Usage**: Monitor application performance, uptime, resource usage
- **Potential**: Create dashboards for MCP Finance health

### Cloud Trace API (`cloudtrace.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Distributed tracing for request flows
- **Usage**: Understand performance bottlenecks across services
- **Integration**: Trace API calls from frontend to backend to database

---

## 🔐 Security & Identity Services

### Identity and Access Management API (`iam.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Manage user roles and permissions
- **Usage**: Control who can access GCP resources
- **Critical**: For production security and compliance

### IAM Service Account Credentials API (`iamcredentials.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Generate temporary credentials for service accounts
- **Usage**: Allow Cloud Run to authenticate with other GCP services
- **Integration**: MCP Server uses this for Cloud Run operations

### Firebase Rules API (`firebaserules.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Security rules for Firebase services
- **Usage**: If using Firebase Authentication or Firestore security rules
- **Note**: Project uses Clerk for auth (see project guidelines)

---

## ⚡ Events & Messaging Services

### Cloud Pub/Sub API (`pubsub.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Message queue for event-driven architecture
- **Potential Uses**:
  - Real-time stock price updates
  - Trading event notifications
  - Background job processing
- **Integration**: Could replace or supplement current event handling

### Eventarc API (`eventarc.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Route events from Google Cloud to services
- **Potential**: Trigger actions on database changes, API events

### Cloud Scheduler API (`cloudscheduler.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Scheduled job execution
- **Potential Uses**:
  - Daily market data synchronization
  - Periodic portfolio rebalancing analysis
  - Scheduled reports and notifications

---

## 🌐 Data Integration Services

### Analytics Hub API (`analyticshub.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Share datasets across organizations
- **Usage**: Access public datasets for market research

### Dataform API (`dataform.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Version-controlled data transformation workflows
- **Potential**: Build reproducible ETL pipelines for market data

### Cloud Dataplex API (`dataplex.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Unified data governance and management
- **Usage**: Organize and govern all financial data assets

---

## 🌍 Translation & Language Services

### Cloud Translate API (`translate.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Machine translation
- **Potential**: Support international users with multi-language interface

### Cloud Text-to-Speech API (`texttospeech.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Convert text to audio
- **Potential**: Audio alerts for significant price movements

---

## 🔧 Core & Management Services

### Google Cloud APIs (`cloudapis.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Meta-API for Google Cloud services
- **Usage**: Required for all API interactions

### Cloud Resource Manager API (`cloudresourcemanager.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Manage GCP projects and resources
- **Usage**: Organizational resource management

### Service Usage API (`serviceusage.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Enable/disable services programmatically
- **Usage**: Infrastructure as Code for service management

### Service Management API (`servicemanagement.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Manage API services
- **Usage**: API configuration and versioning

### Legacy Cloud Source Repositories API (`source.googleapis.com`)
- **Status**: ✅ Enabled
- **Purpose**: Cloud-hosted Git repositories
- **Note**: Using GitHub instead (see project on GitHub)

---

## 📋 Recommended Roadmap

### Immediate (In Use)
- ✅ Cloud Run for application deployment
- ✅ Artifact Registry for container images
- ✅ Cloud Logging & Monitoring for observability
- ✅ IAM for access control

### Short Term (Recommended)
- 📍 Cloud Scheduler for background jobs (market data sync)
- 📍 Pub/Sub for real-time event distribution
- 📍 Cloud SQL if moving to managed PostgreSQL

### Medium Term (Consider)
- 🔄 BigQuery for financial analytics and reporting
- 🔄 Vertex AI for predictive analytics
- 🔄 Cloud Trace for performance optimization

### Future (Optional)
- 💡 Dataform for complex ETL pipelines
- 💡 Cloud Translate for internationalization
- 💡 Text-to-Speech for alerts

---

## 🚫 Services Not in Use
None - all 38 services are currently enabled. Consider disabling unused services to reduce costs and complexity:
- Legacy Source Repositories (using GitHub)
- Cloud Datastore (using Firestore instead)
- Container Registry (using Artifact Registry instead)

---

## Notes & Configuration

### Cluster & Region
- All services configured for project `ttb-lang1`
- Default region should be set for Cloud Run deployments

### Security
- All IAM and service accounts properly configured
- Sensitive data protected per project guidelines
- API keys and credentials not stored in this document

### Cost Optimization
- Monitor BigQuery costs (can be expensive at scale)
- Set up billing alerts in Google Cloud Console
- Use committed use discounts for Vertex AI if using ML

---

**Last Updated**: 2025-02-04
**MCP Status**: Cloud Run MCP Server enabled and auto-approved
