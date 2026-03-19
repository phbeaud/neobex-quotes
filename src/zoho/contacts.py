"""Gestion des contacts (clients) Zoho Invoice.

Recherche intelligente + création automatique de clients.
"""
from __future__ import annotations

import requests
from rapidfuzz import fuzz
from src.zoho.auth import get_headers
from src.config import ZOHO_ORG_ID

_BASE_URL = "https://www.zohoapis.com/invoice/v3"


def get_all_contacts() -> list[dict]:
    """Récupère TOUS les contacts Zoho (paginé)."""
    all_contacts = []
    page = 1
    while True:
        resp = requests.get(
            f"{_BASE_URL}/contacts",
            headers=get_headers(),
            params={
                "organization_id": ZOHO_ORG_ID,
                "per_page": 200,
                "page": page,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        contacts = data.get("contacts", [])
        if not contacts:
            break
        all_contacts.extend(contacts)
        if not data.get("page_context", {}).get("has_more_page", False):
            break
        page += 1
    return all_contacts


def search_contacts(query: str) -> list[dict]:
    """Recherche intelligente de contacts par nom (fuzzy).

    Cherche dans tous les contacts Zoho et retourne les meilleurs
    matches triés par score de similarité.

    Args:
        query: Nom ou partie du nom du client

    Returns:
        Liste de dicts avec contact_id, contact_name, score, email
        Triée par score décroissant. Seuil minimum: 50%.
    """
    all_contacts = get_all_contacts()
    query_lower = query.lower().strip()

    results = []
    for contact in all_contacts:
        name = contact.get("contact_name", "")
        name_lower = name.lower()

        # Score combiné: partial_ratio (trouve "Rose" dans "Rose d'Or")
        # + token_sort_ratio (ordre des mots flexible)
        score_partial = fuzz.partial_ratio(query_lower, name_lower)
        score_token = fuzz.token_sort_ratio(query_lower, name_lower)
        score = max(score_partial, score_token)

        # Bonus si le query est contenu exactement dans le nom
        if query_lower in name_lower:
            score = min(score + 15, 100)

        if score >= 50:
            results.append({
                "contact_id": contact.get("contact_id"),
                "contact_name": name,
                "company_name": contact.get("company_name", ""),
                "email": contact.get("email", ""),
                "score": score,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:10]


def find_or_create_contact(name: str, auto_create: bool = True) -> dict:
    """Cherche un contact par nom. Le crée s'il n'existe pas.

    Args:
        name: Nom du client
        auto_create: Si True, crée le contact automatiquement s'il n'existe pas

    Returns:
        dict avec contact_id et contact_name
    """
    matches = search_contacts(name)

    # Match exact ou très proche (≥90%) → utiliser directement
    if matches and matches[0]["score"] >= 90:
        best = matches[0]
        return {
            "contact_id": best["contact_id"],
            "contact_name": best["contact_name"],
            "created": False,
            "score": best["score"],
        }

    # Pas de bon match → créer le contact
    if auto_create:
        new_contact = create_contact(name)
        return {
            "contact_id": new_contact["contact_id"],
            "contact_name": new_contact["contact_name"],
            "created": True,
            "score": 100,
        }

    # Pas de match et pas de création auto
    return {
        "contact_id": None,
        "contact_name": name,
        "created": False,
        "score": matches[0]["score"] if matches else 0,
        "suggestions": matches[:5],
    }


def create_contact(
    name: str,
    email: str = None,
    phone: str = None,
    company: str = None,
) -> dict:
    """Crée un nouveau contact dans Zoho Invoice.

    Args:
        name: Nom du contact (obligatoire)
        email: Email (optionnel)
        phone: Téléphone (optionnel)
        company: Nom de l'entreprise (optionnel)

    Returns:
        dict du contact créé avec contact_id et contact_name
    """
    payload = {
        "contact_name": name,
        "contact_type": "customer",
    }

    if company:
        payload["company_name"] = company
    if email:
        payload["email"] = email
    if phone:
        payload["phone"] = phone

    resp = requests.post(
        f"{_BASE_URL}/contacts",
        headers=get_headers(),
        params={"organization_id": ZOHO_ORG_ID},
        json=payload,
    )
    data = resp.json()

    if resp.status_code >= 400 or data.get("code") != 0:
        raise RuntimeError(f"Erreur création contact: {data.get('message', resp.text)}")

    contact = data.get("contact", {})
    return {
        "contact_id": contact.get("contact_id"),
        "contact_name": contact.get("contact_name"),
    }
