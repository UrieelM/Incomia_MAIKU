from sqlalchemy.orm import Session
from models.domain import FinancialState, Transaction

# Configuraciones del algoritmo de resiliencia
SAFETY_FACTOR = 0.8 # Para ser conservadores iniciales y no sobreestimar (80%)
RESILIENCE_MONTHS = 3 # M = Número de meses de colchón financiero
MIN_SALARY_THRESHOLD = 200.0 # Umbral mínimo de vida configurable

def process_income_event(db: Session, user_id: int, amount: float) -> dict:
    # O(1) tiempo de ejecución obteniendo estado actual
    financial_state = db.query(FinancialState).filter(FinancialState.user_id == user_id).first()
    
    # 1. Edge Case: Usuario nuevo sin historial
    if not financial_state:
        # Se define un salario objetivo constante y robusto inicial con base al ingreso
        target_salary = amount * SAFETY_FACTOR
        target_salary = max(target_salary, MIN_SALARY_THRESHOLD)
        
        financial_state = FinancialState(
            user_id=user_id, 
            current_artificial_salary=target_salary, 
            available_fund=0.0
        )
        db.add(financial_state)
        # Flush no es estrictamente necesario, pero garantiza que SQLAlchemy maneja el objeto adjunto
    else:
        # En vez de un promedio móvil hiper-reactivo, este modelo RESPETA el S_target constante
        target_salary = financial_state.current_artificial_salary

    artificial_salary_paid = 0.0
    surplus_to_fund = 0.0
    withdrawn_from_fund = 0.0
    
    # F_target conceptual (hasta este punto estamos cubiertos, no hay cap explícito en los reqs)
    # expected_fund_target = target_salary * RESILIENCE_MONTHS

    # 3. Lógica principal de Buffer y Absorsión
    if amount >= target_salary:
        # Ingresos altos: Absorbemos excedentes para construir resiliencia
        artificial_salary_paid = target_salary
        surplus_to_fund = amount - target_salary
        financial_state.available_fund += surplus_to_fund
    else:
        # Ingresos bajos: El fondo entra a funcionar como buffer
        deficit = target_salary - amount
        available_fund = financial_state.available_fund

        if available_fund >= deficit:
            # Fondo es suficiente para mantener el estilo de vida intacto
            withdrawn_from_fund = deficit
            financial_state.available_fund -= deficit
            artificial_salary_paid = target_salary
        else:
            # Fondo se drenó, pagamos lo que entró + resto del fondo
            withdrawn_from_fund = available_fund
            financial_state.available_fund = 0.0
            # artificial_salary_paid no puede ser menor a I_t pq se da integro
            artificial_salary_paid = amount + withdrawn_from_fund
            
            # REACCIÓN A LA REALIDAD: Como el fondo se acabó, el usuario no puede mantener este estilo.
            # Ajustamos el salario objetivo hacia abajo para que meses futuros más reales puedan volver a fondear.
            new_target = (target_salary + artificial_salary_paid) / 2.0
            target_salary = max(new_target, MIN_SALARY_THRESHOLD)
            financial_state.current_artificial_salary = target_salary

    # El nivel de vida NO se expande automáticamente hacia arriba con el éxito (se construye fondo sólido primero).
    # En la aplicación real, el usuario elegirá manualmente cuándo subir su estilo de vida.

    # 4. Asegurarse que estado es correcto y no negativo
    financial_state.available_fund = max(0.0, financial_state.available_fund)
    
    # 5. Calcular indicador de resiliencia
    resilience_indicator = 0.0
    if target_salary > 0:
        resilience_indicator = financial_state.available_fund / target_salary

    # 6. Persistencia de transacciones del bloque
    new_transaction = Transaction(
        user_id=user_id,
        amount=amount,
        target_salary_at_time=target_salary
    )
    db.add(new_transaction)
    db.commit()

    return {
        "amount_processed": amount,
        "artificial_salary_paid": artificial_salary_paid,
        "surplus_to_fund": surplus_to_fund,
        "withdrawn_from_fund": withdrawn_from_fund,
        "current_target": target_salary,
        "remaining_fund": financial_state.available_fund,
        "resilience_indicator": resilience_indicator
    }
