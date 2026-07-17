# -*- coding: utf-8 -*-
"""
Cliente del Service Layer de SAP Business One — Módulo de integración real.
============================================================================
Listo para conectar en cuanto Bexap confirme el Service Layer y Frios
entregue accesos (Fase 0). No lo usa el demo: el demo simula SAP.

Configuración por variables de entorno (o .streamlit/secrets.toml):
    SAP_SL_URL      p.ej. https://servidor-frios:50000/b1s/v1
    SAP_SL_COMPANY  base de datos de la empresa (CompanyDB)
    SAP_SL_USER     usuario de integración
    SAP_SL_PASSWORD contraseña

Uso:
    from sap_service_layer import ServiceLayer
    sl = ServiceLayer.desde_entorno()
    sl.login()
    pagos = sl.pagos_proveedores("2025-05-01", "2025-05-31")
    facturas = sl.facturas_proveedores("2025-05-01", "2025-05-31")
    sl.logout()
"""

import os
from datetime import datetime

import pandas as pd
import requests


class ServiceLayer:
    """Cliente mínimo del Service Layer (OData) de SAP Business One 10.x."""

    def __init__(self, url: str, company: str, user: str, password: str,
                 verificar_ssl: bool = False, timeout: int = 60):
        self.url = url.rstrip("/")
        self.company = company
        self.user = user
        self.password = password
        self.timeout = timeout
        self.sesion = requests.Session()
        self.sesion.verify = verificar_ssl  # instalaciones on-premise suelen usar certificado propio

    @classmethod
    def desde_entorno(cls) -> "ServiceLayer":
        faltan = [v for v in ("SAP_SL_URL", "SAP_SL_COMPANY", "SAP_SL_USER", "SAP_SL_PASSWORD")
                  if not os.environ.get(v)]
        if faltan:
            raise EnvironmentError(f"Faltan variables de entorno: {', '.join(faltan)}")
        return cls(
            url=os.environ["SAP_SL_URL"],
            company=os.environ["SAP_SL_COMPANY"],
            user=os.environ["SAP_SL_USER"],
            password=os.environ["SAP_SL_PASSWORD"],
        )

    # ------------------------------------------------------------------ #
    # Sesión
    # ------------------------------------------------------------------ #
    def login(self) -> None:
        r = self.sesion.post(
            f"{self.url}/Login",
            json={"CompanyDB": self.company, "UserName": self.user, "Password": self.password},
            timeout=self.timeout,
        )
        r.raise_for_status()  # la cookie B1SESSION queda en la sesión

    def logout(self) -> None:
        try:
            self.sesion.post(f"{self.url}/Logout", timeout=self.timeout)
        except requests.RequestException:
            pass

    # ------------------------------------------------------------------ #
    # Consultas paginadas (OData)
    # ------------------------------------------------------------------ #
    def _get_todos(self, recurso: str, params: dict) -> list[dict]:
        registros, url, primera = [], f"{self.url}/{recurso}", True
        while url:
            r = self.sesion.get(url, params=params if primera else None, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            registros.extend(data.get("value", []))
            siguiente = data.get("odata.nextLink") or data.get("@odata.nextLink")
            url = f"{self.url}/{siguiente}" if siguiente else None
            primera = False
        return registros

    # ------------------------------------------------------------------ #
    # Extracciones para la conciliación
    # ------------------------------------------------------------------ #
    def pagos_proveedores(self, desde: str, hasta: str) -> pd.DataFrame:
        """Pagos efectuados (VendorPayments) del periodo — equivale a la
        hoja '1.3 Pagos con UUID' del papel de trabajo."""
        registros = self._get_todos("VendorPayments", {
            "$filter": f"DocDate ge '{desde}' and DocDate le '{hasta}' and Cancelled eq 'tNO'",
            "$select": "DocEntry,DocNum,DocDate,CardCode,CardName,DocTotal,"
                       "TransferAccount,TransferSum,JournalRemarks,PaymentInvoices",
        })
        filas = []
        for p in registros:
            for fac in p.get("PaymentInvoices") or [{}]:
                filas.append({
                    "NÚMERO DE PAGO SISTEMA": p.get("DocNum"),
                    "FECHA DE PAGO SISTEMA": p.get("DocDate"),
                    "NÚMERO DE PROVEEDOR": p.get("CardCode"),
                    "PROVEEDOR": p.get("CardName"),
                    "TOTAL PAGO": p.get("DocTotal"),
                    "CUENTA CONTABLE": p.get("TransferAccount"),
                    "FACTURA (DocEntry)": fac.get("DocEntry"),
                    "IMPORTE APLICADO": fac.get("SumApplied"),
                })
        return pd.DataFrame(filas)

    def facturas_proveedores(self, desde: str, hasta: str) -> pd.DataFrame:
        """Facturas de proveedores (PurchaseInvoices) con UUID fiscal —
        para el cruce contra los CFDIs del SAT."""
        registros = self._get_todos("PurchaseInvoices", {
            "$filter": f"DocDate ge '{desde}' and DocDate le '{hasta}' and Cancelled eq 'tNO'",
            "$select": "DocEntry,DocNum,DocDate,CardCode,CardName,DocTotal,VatSum,"
                       "NumAtCard,U_UUID,FederalTaxID",
        })
        df = pd.DataFrame(registros)
        if not df.empty:
            df = df.rename(columns={
                "NumAtCard": "FOLIO EXTERNO", "U_UUID": "UUID",
                "FederalTaxID": "RFC", "VatSum": "IVA", "DocTotal": "TOTAL FACTURA",
            })
        return df

    def prueba_conexion(self) -> dict:
        """Diagnóstico rápido para la Fase 0: versión y compañía."""
        inicio = datetime.now()
        self.login()
        ms = (datetime.now() - inicio).total_seconds() * 1000
        return {"conectado": True, "empresa": self.company, "latencia_ms": round(ms)}
