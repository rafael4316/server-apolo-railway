import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError
import bcrypt
import datetime
import uvicorn

# Configuración del logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Configuración de la base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no definida")

engine = create_engine(
    DATABASE_URL,
    echo=False
)


Session = sessionmaker(bind=engine)
Base = declarative_base()

# Modelo de Licencia
class License(Base):
    __tablename__ = 'licenses'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    license_key = Column(String, nullable=False)
    expiration_date = Column(Date, nullable=True)
    machine_id = Column(String, default="")
    active = Column(Boolean, default=True)  # 👈 SUSPENSIÓN   


# Instancia de FastAPI
app = FastAPI()

# Modelos Pydantic
class VerifyRequest(BaseModel):
    username: str
    password: str
    license_key: str
    machine_id: str

class ResetRequest(BaseModel):
    admin_token: str
    username: str

class CreateLicenseRequest(BaseModel):
    admin_token: str
    username: str
    password: str
    license_key: str
    expiration_date: str  # Formato "YYYY-MM-DD"
    
    
class RenewRequest(BaseModel):
    admin_token: str
    username: str
    new_expiration_date: str  # YYYY-MM-DD
    
    
    
    
@app.on_event("startup")
def startup():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos inicializada correctamente")
    except OperationalError as e:
        logger.error(f"No se pudo conectar a la base de datos: {e}")

# Endpoint de verificación de licencia
@app.post("/verify")
async def verify_license(data: VerifyRequest):
    session = Session()
    try:
        lic = session.query(License).filter_by(username=data.username).first()

        if not lic:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        if not bcrypt.checkpw(
            data.password.encode(),
            lic.password_hash.encode()
        ):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta.")

        if lic.license_key != data.license_key:
            raise HTTPException(status_code=401, detail="Clave de licencia incorrecta.")

        # 🚫 Licencia suspendida
        if not lic.active:
            raise HTTPException(
                status_code=401,
                detail="Licencia suspendida por falta de pago."
            )

        # 🖥️ Validación de máquina
        if not lic.machine_id:
            lic.machine_id = data.machine_id
            session.commit()
        elif lic.machine_id != data.machine_id:
            raise HTTPException(
                status_code=401,
                detail="La licencia no corresponde a esta máquina."
            )

        # ⏰ Expiración
        if lic.expiration_date and datetime.date.today() > lic.expiration_date:
            raise HTTPException(status_code=401, detail="La licencia ha expirado.")

        return {
            "success": True,
            "message": "Licencia válida.",
            "expiration_date": (
                lic.expiration_date.isoformat()
                if lic.expiration_date else None
            )
        }

    finally:
        session.close()
        
        

@app.post("/renew_license")
async def renew_license(data: RenewRequest):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

    if not ADMIN_TOKEN:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN no configurado.")

    if data.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado.")

    session = Session()
    try:
        lic = session.query(License).filter_by(username=data.username).first()
        if not lic:
            raise HTTPException(status_code=404, detail="Licencia no encontrada.")

        lic.expiration_date = datetime.date.fromisoformat(
            data.new_expiration_date
        )

        session.commit()

        return {
            "success": True,
            "message": "Licencia renovada correctamente.",
            "new_expiration_date": lic.expiration_date.isoformat()
        }

    finally:
        session.close()

# Endpoint para resetear licencia
@app.post("/reset_license")
async def reset_license(data: ResetRequest):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

    if not ADMIN_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="ADMIN_TOKEN no configurado en el servidor."
        )

    if data.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado.")

    session = Session()
    try:
        lic = session.query(License).filter_by(username=data.username).first()
        if not lic:
            raise HTTPException(status_code=404, detail="Licencia no encontrada.")

        lic.machine_id = ""   # 🔄 libera la máquina
        session.commit()

        return {"success": True, "message": "Licencia reiniciada correctamente."}

    finally:
        session.close()



@app.post("/suspend_license")
async def suspend_license(data: ResetRequest):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

    if not ADMIN_TOKEN:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN no configurado.")

    if data.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado.")

    session = Session()
    try:
        lic = session.query(License).filter_by(username=data.username).first()
        if not lic:
            raise HTTPException(status_code=404, detail="Licencia no encontrada.")

        lic.active = False
        session.commit()

        return {"success": True, "message": "Licencia suspendida correctamente."}
    finally:
        session.close()



# Endpoint para crear licencias remotamente
@app.post("/create_license")
async def create_license(data: CreateLicenseRequest):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

    if not ADMIN_TOKEN:
        raise HTTPException(status_code=500, detail="ADMIN_TOKEN no configurado.")

    if data.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado.")

    session = Session()
    try:
        if session.query(License).filter_by(username=data.username).first():
            raise HTTPException(status_code=409, detail="Usuario ya existe.")

        expiration_date = datetime.datetime.fromisoformat(data.expiration_date).date()
        pw_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

        new_license = License(
            username=data.username,
            password_hash=pw_hash,
            license_key=data.license_key,
            expiration_date=expiration_date,
            machine_id=""
        )

        session.add(new_license)
        session.commit()

        return {"success": True, "message": "Licencia creada correctamente."}

    finally:
        session.close()


@app.get("/licenses")
async def list_licenses(admin_token: str):
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
    if not ADMIN_TOKEN or admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado.")

    session = Session()
    try:
        licenses = session.query(License).all()

        return [
            {
                "username": lic.username,
                "license_key": lic.license_key,
                "machine_id": lic.machine_id,
                "expiration_date": (
                    lic.expiration_date.isoformat()
                    if lic.expiration_date else None
                ),
                "active": lic.active
            }
            for lic in licenses
        ]
    finally:
        session.close()



# Endpoint raíz para comprobación rápida
@app.get("/")
async def root():
    return {"message": "API de licencias al aire ✔️"}

# Arranque de Uvicorn
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
        access_log=True
    )

