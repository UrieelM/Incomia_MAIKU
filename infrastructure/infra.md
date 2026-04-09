# Infraestructura Incomia (Proyecto HAIKU)

Bienvenido a la documentación de infraestructura del proyecto Incomia. Este documento explica detalle a detalle los servicios aprovisionados en AWS utilizando Terraform, el objetivo de cada uno, por qué los elegimos y cómo se interconectan.

---

## Resumen de Servicios Creados

En este proyecto, separamos la lógica de negocio en la nube agrupando responsabilidades en cinco módulos principales:

### 1. **Amazon DynamoDB (Base de Datos)**
* **Ubicación:** Directorio `modules/dynamodb/`
* **¿Qué es?:** Una base de datos NoSQL serverless de llave-valor y documentos que ofrece rendimiento super rápido (milisegundos de un dígito a cualquier escala).
* **¿Para qué se creó?:** Para almacenar el estado seguro de los usuarios (tabla `users`) y su historial de movimientos/pagos (tabla `transactions`).
* **Objetivo y Funcionamiento:** DynamoDB garantiza latencias ultra bajas y escalabilidad automática para lecturas/escrituras. Configuramos ambas tablas como `PAY_PER_REQUEST` (pago por solicitud) para minimizar costos cuando hay poco tráfico, ideal para etapas de desarrollo y crecimiento orgánico.

### 2. **Amazon S3 (Almacenamiento y Alojamiento)**
* **Ubicación:** Directorio `modules/s3/`
* **¿Qué es?:** Un servicio de almacenamiento de objetos con seguridad líder en la industria.
* **¿Para qué se creó?:** En este proyecto tiene dos propósitos:
    1. **Frontend Hosting:** Alojar toda la aplicación estática en React (archivos HTML, CSS y JS).
    2. **Data Lake:** Servir como repositorio central (`datalake`) para almacenar información cruda, logs, reportes, imágenes u otro tipo de eventos no estructurados que debamos procesar después.
* **Objetivo y Funcionamiento:** Mantiene separados los archivos compilados del equipo Frontend del almacenamiento persistente del backend. El bucket del Data Lake cuenta con **versionamiento activado** para nunca perder la procedencia de la data.

### 3. **Amazon Cognito (Identidad y Autenticación)**
* **Ubicación:** Directorio `modules/cognito/`
* **¿Qué es?:** Un servicio completo para la administración de identidad de usuarios (IAM) en aplicaciones web/móviles.
* **¿Para qué se creó?:** Para manejar los flujos de "Registro" y "Login" (signIn, signUp) sin preocuparnos por administrar bases de datos de contraseñas.
* **Objetivo y Funcionamiento:** Genera y valida de manera automática los tokens temporales (JWT). El **User Pool** sirve como nuestro directorio de usuarios, y el **User Pool Client** es la interfaz que permite que la capa de React interactúe con el proceso de credenciales para obtener acceso limpio utilizando la validación de correo electrónico.

### 4. **API Gateway (Enrutamiento HTTP)**
* **Ubicación:** Directorio `modules/api_gateway/`
* **¿Qué es?:** El punto central de entrada al ecosistema backend, configurado como una API HTTP super optimizada y económica.
* **¿Para qué se creó?:** Sirve como una "puerta" hacia nuestras funciones Lambda. Define cómo el frontend va a hacer peticiones REST al servidor.
* **Objetivo y Funcionamiento:** Aquí aseguramos todas nuestras rutas. Cuenta con un **Authorizer de JWT** que está estrictamente enlazado a Cognito. Esto significa que antes de que siquiera se detone nuestra lógica en Lambda (ahorrando tiempo de cómputo), API Gateway filtra e impide que cualquier petición sin un token de Cognito válido pueda ingresar a nuestra infraestructura. Adicionalmente, cuenta con soporte base para los protocolos CORS necesarios para permitir solicitudes del front.

### 5. **IAM para Lambdas (Gestión de Seguridad Backend)**
* **Ubicación:** Archivo `iam.tf` en la raíz de infraestructura
* **¿Qué es?:** Rol de seguridad estricto que rige cómo interactúan las piezas en la nube.
* **¿Para qué se creó?:** Para inyectar de manera segura permisos al código del equipo de Backend (Serverless Lambdas).
* **Objetivo y Funcionamiento:** Por defecto en AWS, ningún servicio puede hablar con otro. Con este rol IAM, permitimos que el backend de funciones Lambda logre hacer lecturas/escrituras en **DynamoDB**, mover archivos al **Data Lake en S3**, hablar con la inteligencia artificial usando **Amazon Bedrock**, y registrar toda su actividad vital en **CloudWatch Logs**. Todo basado en el "principio de menor privilegio" para mantener un escudo robusto sobre la red.

---

##  Archivo de Configuración Local y Flujo

Para desplegar estos servicios de acuerdo al estándar utilizado:
1. Crea tu bucket S3 manual para el estado (`incomia-tfstate`).
2. Configura los valores en el archivo `.tfvars`.
3. Inicia terraform con `terraform init`.
4. Ejecuta `terraform apply` para leer toda esta infraestructura que será replicada fielmente.

El backend enviará todos las credenciales finales de generación (Endpoints, IDs y ARNs) a tu `.env.example` en formato salida (`outputs.tf`).
