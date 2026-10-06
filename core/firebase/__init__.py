# -*- coding: utf-8 -*-
"""
Pacote Firebase — Aetheris ToolBox
==================================
Serviços e utilitários para integração com Firebase (Auth, Firestore, Storage).
"""

from __future__ import annotations

from core.firebase.FirebaseConfig import FirebaseConfig
from core.firebase.FirebaseAuthService import FirebaseAuthService
from core.firebase.FirebaseServiceAccountAuth import FirebaseServiceAccountAuth
from core.firebase.FirebaseTokenProvider import FirebaseTokenProvider
from core.firebase.FirestoreService import FirestoreService
from core.firebase.CloudDatabaseSync import CloudDatabaseSync
from core.firebase.FirebaseStorageService import FirebaseStorageService
from core.firebase.FirebaseWorker import FirebaseWorker
from core.firebase.FirebaseCredentialManager import FirebaseCredentialManager

__all__ = [
    "FirebaseConfig",
    "FirebaseAuthService",
    "FirebaseServiceAccountAuth",
    "FirebaseTokenProvider",
    "FirestoreService",
    "CloudDatabaseSync",
    "FirebaseStorageService",
    "FirebaseWorker",
    "FirebaseCredentialManager",
]
