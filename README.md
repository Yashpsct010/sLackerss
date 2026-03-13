# sLackerss — AI-Powered Demand Intelligence Copilot

An end-to-end, AI-driven supply chain optimization platform designed to eliminate stockouts and minimize overstock through predictive demand analytics and automated inventory management.

## 🚀 Key Features

- **XGBoost Forecasting Engine:** Generates 30-day demand predictions with statistical confidence intervals (P10/P90 bands).
- **Proactive Inventory Optimizer:** Autonomous calculation of Economic Order Quantity (EOQ), Safety Stock, and Reorder Points.
- **Decision Dashboard:** Real-time visibility into SKU-level risk factors and stockout alerts built with Next.js.
- **1-Click Restock:** actionable intelligence that allows procurement managers to execute orders directly from the UI.
- **Cloud Scale:** Fully containerized and optimized for AWS serverless and multi-container deployment.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.10, FastAPI, Mangum |
| **Data Science** | XGBoost, Scikit-learn, Pandas, Prophete, NumPy |
| **Frontend** | Next.js 14 (App Router), React, Recharts, Tailwind CSS |
| **Infrastructure** | Docker, Docker Compose, AWS Elastic Beanstalk, ECR |
| **Storage** | Amazon DynamoDB (NoSQL), Amazon S3 (ML Artifacts), SQLite (Local) |

---

## 💻 Local Development Setup

The easiest way to run the entire stack locally is using **Docker Compose**.

### Prerequisites
- Docker & Docker Compose installed
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Yashpsct010/sLackerss.git
cd sLackerss
```

### 2. Run with Docker Compose
```bash
docker-compose up --build
```

- **Frontend:** [http://localhost](http://localhost) (mapped to port 80/3000)
- **API (FastAPI):** [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger Documentation)

---

## ☁️ AWS Deployment Architecture

This solution is engineered to be cloud-native and highly scalable on AWS.

### Infrastructure Components
- **AWS Elastic Beanstalk:** Orchestrates the multi-container environment on Amazon Linux 2023.
- **Amazon ECR (Registry):** To bypass heavy build timeouts on the cloud server, we pre-build our Machine Learning Docker images locally and push them to ECR repositories.
- **Amazon DynamoDB:** Handles high-velocity sales telemetry and manages the live state of SKU inventory with millisecond latency.
- **Amazon S3:** Used for storing trained XGBoost `.joblib` model artifacts, ensuring the API instances remain stateless and scalable.

### Deployment Workflow
1. **Push Images to ECR:** Build and tag the `frontend` and `backend` images and push them to their respective ECR repositories.
2. **Configure Environment:** Set up the required environment properties in Elastic Beanstalk (e.g., `DOCKER_ENV=true`, `NEXT_PUBLIC_API_URL`).
3. **ZIP & Deploy:** Create a deployment package containing only the `docker-compose.yml` (pointing to the ECR images) and the `.ebextensions/` folder.
4. **IAM Roles:** Attach the `AmazonEC2ContainerRegistryReadOnly` policy to the `aws-elasticbeanstalk-ec2-role` to allow the environment to pull the private images.

---

## 📈 Accuracy & Training
The system includes an `Accuracy Tracker` and automated retraining pipeline. As live sales data flows into DynamoDB, the system calculates the **WMAPE (Weighted Mean Absolute Percentage Error)** and automatically triggers model retraining via Amazon S3 once data drift exceeds predefined thresholds.

---

## 👥 Contributors
- **The sLackerss Team**
