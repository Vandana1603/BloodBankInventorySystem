#  National Blood Grid & Predictive Inventory System
**An Automated Cloud-Native Geospatial Analytics Engine on AWS**

1. Architecture Flow and Data Pipeline
   Stage 1: Ingestion and SchedulingExternal Source: The pipeline pulls live nationwide blood bank data from the Data.gov.in REST API.
   Automation Trigger: Amazon EventBridge functions as a serverless cron scheduler to initiate the ingestion loop automatically every 30 minutes.
   Processing Core: AWS Lambda processes the raw data payload out-of-band without managing physical server setups.

   Stage 2: Security and Database PersistenceSecret Management: AWS Systems Manager Parameter Store securely decrypts and provisions the external API access keys at runtime.
   Database Writes: AWS Lambda uses high-efficiency batch writing loops to stream 1,000+ normalized records into the database at once.
   Storage Backbone: Amazon DynamoDB acts as the NoSQL data layer, using composite primary keys to store medical attributes under sub-millisecond query latencies.

   Stage 3: Visual Analytics and AI InferenceProgrammatic Link: The Streamlit UI Engine initializes a secure programmatic SDK session via Boto3 to read from the DynamoDB data layer.
   Geospatial Layer: Streamlit streams coordinates into a Folium Heatmap to process multi-point clustering layouts smoothly.
   Machine Learning Integration: The dashboard makes real-time REST API calls to an active Amazon SageMaker Canvas endpoint to execute predictive supply-chain demand forecasting.

   2. Core AWS Cloud Framework

*   **AWS Lambda (Python 3.12)**: Serverless processing of external raw JSON data payloads.
*   **Amazon EventBridge**: Cron scheduler managing hands-free automated pipeline execution loops.
*   **AWS Systems Manager (SSM)**: Secure Parameter Store keeping app API keys encrypted at rest.
*   **Amazon DynamoDB**: Distributed NoSQL layer ensuring sub-millisecond query latency.
*   **Amazon SageMaker Canvas**: Real-time AutoML engine generating 48-hour continuous numeric forecasts.


## 3. Key Visualizations & Analytics
*   **Visual 1: Geospatial Hotspot Map**: Combines a Folium HeatMap with Marker Clusters for lag-free rendering.
*   **Visual 2: Supply-Chain Metrics**: Deploys multi-tier Plotly Sunburst charts to show sector distributions.
*   **Visual 3: Healthcare Gap Finder**: Automatically scans and highlights geographical "Care Deserts".
*   **Advanced Feature: SageMaker AI Audit**: Calls real-time hosted ML instance endpoints for stock alerts.

-[VANDANA K]
