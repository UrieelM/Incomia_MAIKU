# Incomia: Estabilidad Financiera para la Gig Economy

> *Suavizando ingresos volátiles con IA y Arquitectura Serverless en AWS.*

![AWS](https://img.shields.io/badge/AWS-%23232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-%23005571?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-%2320232A?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-%23007ACC?style=for-the-badge&logo=typescript&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-%23623CE4?style=for-the-badge&logo=terraform&logoColor=white)

---

## 🚀 Misión del Proyecto
**Incomia** es una plataforma *fintech* diseñada específicamente para trabajadores independientes y freelancers en México. Nuestra misión es eliminar la incertidumbre financiera mediante la **suavización de ingresos**: simulamos un salario estable calculando promedios y gestionando reservas dinámicas. Con el poder de **Amazon Bedrock**, proporcionamos asesoría financiera personalizada y análisis de gastos en tiempo real.

---

## 📂 Estructura del Repositorio

A diferencia de versiones anteriores, esta estructura refleja fielmente el estado actual del proyecto:

```text
.
├── 🧠 AI/                          # Motor de Inteligencia Artificial
│   ├── infrastructure/             # Configuración de Athena, EventBridge e IAM para AI
│   ├── advice_generator.py         # Generación de consejos con Amazon Nova Pro
│   ├── data_generator.py           # Generador de datos sintéticos de alta fidelidad
│   ├── liquidity_forecast.py       # Predocción de liquidez a 14 días
│   ├── weekly_alerts.py            # Analizador de gastos discrecionales
│   └── AI.md                       # Documentación técnica del motor de IA
│
├── ⚙️ backend/                      # Backend Serverless (Python/AWS SAM)
│   └── incomia-backend/
│       ├── lambdas/                # Handlers de AWS Lambda
│       │   ├── analyze_expenses/   # Análisis periódico de gastos
│       │   ├── create_user/        # Inicialización de perfiles
│       │   ├── get_ai_advice/      # Puente con el motor de IA
│       │   ├── get_forecast/       # Predicción de liquidez
│       │   ├── log_income/         # Lógica central de suavización de salario
│       │   └── ...                 # (Ver sección de Lambdas para detalle)
│       ├── shared/                 # Código compartido (Bedrock, DB, Adapters)
│       └── template.yaml           # Plantilla de AWS SAM
│
├── 💻 frontend/                     # Aplicación Web (React + Vite + Tailwind)
│   ├── src/                        # Componentes, Páginas y Hooks
│   ├── public/                     # Assets estáticos y logos
│   ├── tailwind.config.js          # Configuración de diseño
│   └── vite.config.ts              # Configuración del Bundler
│
└── ☁️ infrastructure/                # Infraestructura como Código (Terraform)
    ├── modules/                    # Módulos: Cognito, DynamoDB, API GW, etc.
    ├── main.tf                     # Orquestación principal
    ├── iam.tf                      # Seguridad y roles de ejecución
    ├── infra.md                    # Guía detallada de la arquitectura en la nube
    └── terraform.tfvars            # Variables de entorno de infraestructura
```

---

## 🏛️ Arquitectura Técnica

Incomia utiliza un enfoque **Event-Driven Serverless** para garantizar escalabilidad y costos mínimos:

1. **Ingesta**: API Gateway valida tokens JWT vía Amazon Cognito.
2. **Cómputo**: AWS Lambda procesa la lógica de negocio en Python 3.11.
3. **Persistencia**: DynamoDB bajo patrón de tabla única para usuarios y transacciones.
4. **Inteligencia**: Invocaciones a Amazon Bedrock (`amazon.nova-pro-v1:0`) con patrones de *Circuit Breaker* para alta disponibilidad.
5. **Analytics**: Data Lake en S3 procesado por AWS Athena para insights profundos.

---

## 🛠️ Detalle de Funciones Lambda Principales

### 💰 `log_income`
Calcula el "Salario Simulado" basado en una ventana móvil de 6 meses. Si el ingreso supera el promedio, el excedente se mueve automáticamente a una **Reserva de Estabilidad**.

### 🤖 `get_ai_advice`
Utiliza el historial de transacciones y el puntaje de riesgo para generar consejos empáticos y accionables.
* **Trigger**: API Get / EventBridge `ForecastReady`.
* **Respuesta**: Markdown con insights personalizados.

---

## 🛠️ Guía de Desarrollo

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Requisitos: Archivo `.env` configurado con `VITE_API_BASE_URL` y datos de Cognito.

### Backend (Local)
Para invocar lambdas localmente usando AWS SAM:
```bash
cd backend/incomia-backend
sam local invoke "GetDashboardFunction" --event event.json
```

### Infraestructura
Para desplegar cambios en la nube:
```bash
cd infrastructure
terraform init
terraform apply
```

---

## 🛡️ Seguridad e IAM
El sistema se adhiere al principio de **Privilegio Mínimo**. Los roles `lambda_exec` están restringidos a los recursos específicos del proyecto `incomia-*` en DynamoDB, S3 y SSM.

---

## 📝 Referencia de API (Endpoints Críticos)

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `POST` | `/users` | Registro inicial de usuario. |
| `POST` | `/users/{id}/income` | Registro de ingreso + Cómputo de reserva. |
| `GET` | `/users/{id}/dashboard`| Vista consolidada (Next Payday, Balances). |
| `GET` | `/users/{id}/ai/advice`| Asesoría financiera impulsada por IA. |

---

<div align="center">
  <sub>Desarrollado para el Talent Land 2026. Proyecto Incomia.</sub>
</div>