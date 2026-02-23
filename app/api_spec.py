from __future__ import annotations

# OpenAPI Spec (Swagger liest das 1:1).
SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "ScootCity API",
        "version": "1.0.0",
        "description": "REST API für Fahrzeuge, Fahrten und Authentisierung der ScootCity Plattform.",
    },
    "servers": [
        {"url": "http://localhost:5000", "description": "Lokale Entwicklung"}
    ],
    "tags": [
        {"name": "Accounts", "description": "User- und Provider-Verwaltung"},
        {"name": "Auth", "description": "Authentisierung & Token"},
        {"name": "Vehicles", "description": "Fahrzeugflotte verwalten"},
        {"name": "Rides", "description": "Fahrten starten, beenden und auslesen"},
        {"name": "Payments", "description": "Zahlungsmittel verwalten"}
    ],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "Token"
            }
        },
        "schemas": {
            "Vehicle": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "provider_id": {"type": "integer"},
                    "vehicle_type": {"type": "string"},
                    "status": {"type": "string"},
                    "battery_level": {"type": "number"},
                    "gps_lat": {"type": "number"},
                    "gps_long": {"type": "number"},
                    "qr_code": {"type": "string"}
                }
            },
            "Ride": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "user_id": {"type": "integer"},
                    "vehicle_id": {"type": "integer"},
                    "start_time": {"type": "string", "format": "date-time"},
                    "end_time": {"type": "string", "format": "date-time", "nullable": True},
                    "kilometers": {"type": "number"},
                    "cost": {"type": "number"}
                }
            },
            "PaymentMethod": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "type": {"type": "string"},
                    "details": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time", "nullable": True},
                    "is_active": {"type": "boolean"}
                }
            },
        },
    },
    "paths": {
        "/api/users": {
            "post": {
                "tags": ["Accounts"],
                "summary": "Registriert einen neuen Rider-Account",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string"}
                                },
                                "required": ["name", "email", "password"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "User erstellt + Token zurückgegeben"},
                    "409": {"description": "E-Mail existiert bereits"}
                }
            }
        },
        "/api/providers": {
            "post": {
                "tags": ["Accounts"],
                "summary": "Registriert einen neuen Provider",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string"},
                                    "typ": {"type": "string"}
                                },
                                "required": ["name", "email", "password"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Provider erstellt + Token zurückgegeben"},
                    "409": {"description": "E-Mail existiert bereits"}
                }
            }
        },
        "/api/token": {
            "post": {
                "tags": ["Auth"],
                "summary": "Erzeuge ein API Token",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string"},
                                    "account_type": {"type": "string", "enum": ["user", "provider"]}
                                },
                                "required": ["email", "password"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Token erstellt",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "token": {"type": "string"},
                                        "role": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Ungültige Zugangsdaten"}
                }
            }
        },
        "/api/vehicles": {
            "get": {
                "tags": ["Vehicles"],
                "summary": "Liste Fahrzeuge",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "status",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Optionaler Statusfilter"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Liste der Fahrzeuge",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Vehicle"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Token fehlt oder ungültig"}
                }
            },
            "post": {
                "tags": ["Vehicles"],
                "summary": "Legt ein Fahrzeug für den authentifizierten Provider an",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "vehicle_type": {"type": "string"},
                                    "status": {"type": "string"},
                                    "battery_level": {"type": "number"},
                                    "gps_lat": {"type": "number"},
                                    "gps_long": {"type": "number"},
                                    "qr_code": {"type": "string"}
                                },
                                "required": ["qr_code"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Fahrzeug erstellt"},
                    "400": {"description": "Validierungsfehler"},
                    "401": {"description": "Token fehlt oder ungültig"}
                }
            }
        },
        "/api/vehicles/{vehicle_id}": {
            "get": {
                "tags": ["Vehicles"],
                "summary": "Fahrzeugdetails",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "vehicle_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Fahrzeug",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Vehicle"}
                            }
                        }
                    },
                    "403": {"description": "Keine Berechtigung"},
                    "404": {"description": "Nicht gefunden"}
                }
            },
            "patch": {
                "tags": ["Vehicles"],
                "summary": "Aktualisiert ein Fahrzeug (Provider)",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "vehicle_type": {"type": "string"},
                                    "status": {"type": "string"},
                                    "battery_level": {"type": "number"},
                                    "gps_lat": {"type": "number"},
                                    "gps_long": {"type": "number"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Fahrzeug aktualisiert"},
                    "403": {"description": "Keine Berechtigung"}
                }
            },
            "delete": {
                "tags": ["Vehicles"],
                "summary": "Löscht ein Fahrzeug (Provider)",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {"description": "Gelöscht"},
                    "403": {"description": "Keine Berechtigung"}
                }
            }
        },
        "/api/vehicles/{vehicle_id}/qr": {
            "get": {
                "tags": ["Vehicles"],
                "summary": "Liefert den QR-Code eines Fahrzeugs als PNG",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "vehicle_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "PNG mit QR-Code",
                        "content": {
                            "image/png": {}
                        }
                    },
                    "403": {"description": "Keine Berechtigung"},
                    "404": {"description": "Nicht gefunden"}
                }
            }
        },
        "/api/rides": {
            "get": {
                "tags": ["Rides"],
                "summary": "Liste Fahrten des angemeldeten Users",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Fahrtenliste",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Ride"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Token fehlt oder ungültig"}
                }
            }
        },
        "/api/rides/start": {
            "post": {
                "tags": ["Rides"],
                "summary": "Startet eine Fahrt",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "vehicle_id": {"type": "integer"}
                                },
                                "required": ["vehicle_id"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Fahrt gestartet"},
                    "400": {"description": "Validierungsfehler"}
                }
            }
        },
        "/api/rides/{ride_id}/end": {
            "post": {
                "tags": ["Rides"],
                "summary": "Beendet eine Fahrt",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "ride_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "kilometers": {"type": "number"},
                                    "payment_method_id": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Fahrt beendet"},
                    "400": {"description": "Validierungsfehler"}
                }
            }
        },
        "/api/payment-methods": {
            "get": {
                "tags": ["Payments"],
                "summary": "Listet Zahlungsmittel des Users",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Liste Zahlungsmittel",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/PaymentMethod"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Payments"],
                "summary": "Legt ein Zahlungsmittel an",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "method_type": {"type": "string"},
                                    "details": {"type": "string"}
                                },
                                "required": ["details"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Zahlungsmittel erstellt"}
                }
            }
        },
        "/api/payment-methods/{method_id}": {
            "delete": {
                "tags": ["Payments"],
                "summary": "Löscht ein Zahlungsmittel",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "method_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "200": {"description": "Zahlungsmittel archiviert"},
                    "404": {"description": "Nicht gefunden"}
                }
            }
        },
        "/api/vehicle-types": {
            "get": {
                "tags": ["Vehicles"],
                "summary": "Listet alle registrierten Fahrzeugtypen",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Fahrzeugtypen",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Vehicles"],
                "summary": "Legt einen neuen Fahrzeugtyp an",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"}
                                },
                                "required": ["name"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Typ erstellt"},
                    "400": {"description": "Validierungsfehler"},
                    "409": {"description": "Typ existiert bereits"}
                }
            }
        }
    }
}
