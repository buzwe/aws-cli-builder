from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import botocore.session
import re
import os
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
session = botocore.session.get_session()

def to_kebab_case(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '-', name).lower()

@app.get("/services")
def get_services():
    return session.get_available_services()


@app.get("/operations")
def get_operations(service: str = Query(...)):
    try:
        client = session.create_client(service)
        model = client.meta.service_model

        ops = {}

        for op_name in model.operation_names:
            op_model = model.operation_model(op_name)

            inputs = {}

            if op_model.input_shape:
                for name, shape in op_model.input_shape.members.items():
                    inputs[name] = shape.type_name

            ops[op_name] = inputs

        return ops

    except Exception as e:
        return {"error": str(e)}

@app.post("/generate")
def generate_command(body: dict):
    service = body["service"]
    operation = body["operation"]
    params = body.get("params", {})

    cmd = f"aws {service} {operation.replace('_', '-').lower()}"

    for k, v in params.items():
        if v:
            cmd += f" --{k.lower()} {v}"

    return {"command": cmd}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


