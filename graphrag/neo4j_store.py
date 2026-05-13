"""
Kairós Intelligence v2.7.1 — Neo4j Store
Grafo de conhecimento: pacientes, médicos, especialidades, convênios.
"""

from neo4j import GraphDatabase
from graphrag.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class Neo4jStore:
    """Armazenamento de grafo de conhecimento no Neo4j."""

    def __init__(self):
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()

    # --- Pacientes ---
    def add_patient(self, clinic_id: str, patient: dict):
        """Adiciona ou atualiza paciente no grafo."""
        query = """
        MERGE (p:Patient {cpf: $cpf, clinic: $clinic_id})
        SET p.name = $name,
            p.phone = $phone,
            p.birth_date = $birth_date,
            p.email = $email,
            p.opt_in_tips = $opt_in_tips,
            p.updated_at = datetime()
        RETURN p
        """
        with self.driver.session() as session:
            session.run(query, clinic_id=clinic_id, **patient)

    # --- Médicos ---
    def add_doctor(self, clinic_id: str, doctor: dict):
        """Adiciona ou atualiza médico no grafo."""
        query = """
        MERGE (d:Doctor {name: $name, clinic: $clinic_id})
        SET d.crm = $crm,
            d.schedule = $schedule,
            d.active = $active,
            d.updated_at = datetime()
        WITH d
        UNWIND $specialties AS spec
        MERGE (s:Specialty {name: spec})
        MERGE (d)-[:SPECIALIZES]->(s)
        """
        with self.driver.session() as session:
            session.run(query, clinic_id=clinic_id, **doctor)

    # --- Convênios ---
    def add_insurance(self, clinic_id: str, insurance: dict):
        """Adiciona ou atualiza convênio no grafo."""
        query = """
        MERGE (i:Insurance {name: $name, clinic: $clinic_id})
        SET i.plans = $plans,
            i.active = $active,
            i.updated_at = datetime()
        """
        with self.driver.session() as session:
            session.run(query, clinic_id=clinic_id, **insurance)

    # --- Relações ---
    def link_patient_doctor(self, clinic_id: str, cpf: str, doctor_name: str):
        """Registra que paciente consultou com médico."""
        query = """
        MATCH (p:Patient {cpf: $cpf, clinic: $clinic_id})
        MATCH (d:Doctor {name: $doctor_name, clinic: $clinic_id})
        MERGE (p)-[r:CONSULTED]->(d)
        SET r.last_visit = datetime(),
            r.count = COALESCE(r.count, 0) + 1
        """
        with self.driver.session() as session:
            session.run(
                query, clinic_id=clinic_id, cpf=cpf, doctor_name=doctor_name
            )

    def link_patient_insurance(self, clinic_id: str, cpf: str, insurance_name: str):
        """Registra convênio do paciente."""
        query = """
        MATCH (p:Patient {cpf: $cpf, clinic: $clinic_id})
        MATCH (i:Insurance {name: $insurance_name, clinic: $clinic_id})
        MERGE (p)-[:HAS_INSURANCE]->(i)
        """
        with self.driver.session() as session:
            session.run(
                query, clinic_id=clinic_id, cpf=cpf, insurance_name=insurance_name
            )

    # --- Queries de Contexto ---
    def get_patient_context(self, clinic_id: str, phone: str) -> dict | None:
        """Busca contexto completo do paciente pelo telefone."""
        query = """
        MATCH (p:Patient {phone: $phone, clinic: $clinic_id})
        OPTIONAL MATCH (p)-[c:CONSULTED]->(d:Doctor)-[:SPECIALIZES]->(s:Specialty)
        OPTIONAL MATCH (p)-[:HAS_INSURANCE]->(i:Insurance)
        RETURN p, collect(DISTINCT {doctor: d.name, specialty: s.name, visits: c.count}) AS doctors,
               collect(DISTINCT i.name) AS insurances
        """
        with self.driver.session() as session:
            result = session.run(query, clinic_id=clinic_id, phone=phone)
            record = result.single()
            if record and record["p"]:
                patient = dict(record["p"])
                patient["doctors"] = [d for d in record["doctors"] if d["doctor"]]
                patient["insurances"] = record["insurances"]
                return patient
        return None

    def get_doctors_by_specialty(self, clinic_id: str, specialty: str) -> list[dict]:
        """Busca médicos por especialidade."""
        query = """
        MATCH (d:Doctor {clinic: $clinic_id, active: true})-[:SPECIALIZES]->(s:Specialty)
        WHERE toLower(s.name) CONTAINS toLower($specialty)
        RETURN d.name AS name, d.crm AS crm, d.schedule AS schedule,
               collect(s.name) AS specialties
        """
        with self.driver.session() as session:
            result = session.run(query, clinic_id=clinic_id, specialty=specialty)
            return [dict(record) for record in result]


neo4j_store = Neo4jStore()
