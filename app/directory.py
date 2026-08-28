import json
import os
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/api/directory", tags=["directory"])

_ARF_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "arf.json")
_arf_cache = None


def _load_arf():
    global _arf_cache
    if _arf_cache is None:
        with open(_ARF_PATH, "r", encoding="utf-8") as f:
            _arf_cache = json.load(f)
    return _arf_cache


def _flatten_tools(node, path=None):
    if path is None:
        path = []
    tools = []
    current_path = path + [node.get("name", "")]
    if node.get("type") == "url":
        tools.append({
            "name": node.get("name", ""),
            "url": node.get("url", ""),
            "description": node.get("description", ""),
            "status": node.get("status", "unknown"),
            "pricing": node.get("pricing", "unknown"),
            "bestFor": node.get("bestFor", ""),
            "input": node.get("input", ""),
            "output": node.get("output", ""),
            "opsec": node.get("opsec", "unknown"),
            "opsecNote": node.get("opsecNote", ""),
            "localInstall": node.get("localInstall", False),
            "googleDork": node.get("googleDork", False),
            "registration": node.get("registration", False),
            "editUrl": node.get("editUrl", False),
            "api": node.get("api", False),
            "deprecated": node.get("deprecated", False),
            "invitationOnly": node.get("invitationOnly", False),
            "category": current_path[1] if len(current_path) > 1 else "",
            "subcategory": current_path[2] if len(current_path) > 2 else "",
            "breadcrumb": " > ".join(current_path[1:]),
        })
    for child in node.get("children", []) or []:
        tools.extend(_flatten_tools(child, current_path))
    return tools


def _get_categories(node, depth=0, parent_path=""):
    cats = []
    if node.get("type") == "folder":
        name = node.get("name", "")
        path = f"{parent_path}/{name}" if parent_path else name
        tool_count = len(_flatten_tools(node))
        subcats = []
        for child in node.get("children", []) or []:
            if child.get("type") == "folder":
                subcats.extend(_get_categories(child, depth + 1, path))
        cats.append({
            "name": name,
            "path": path,
            "depth": depth,
            "toolCount": tool_count,
            "children": subcats,
        })
    return cats


@router.get("/stats")
async def directory_stats():
    arf = _load_arf()
    all_tools = _flatten_tools(arf)
    categories = _get_categories(arf)

    pricing = {}
    opsec = {}
    types = {"live": 0, "deprecated": 0, "localInstall": 0, "googleDork": 0, "registration": 0, "api": 0}
    for t in all_tools:
        p = t.get("pricing", "unknown")
        pricing[p] = pricing.get(p, 0) + 1
        o = t.get("opsec", "unknown")
        opsec[o] = opsec.get(o, 0) + 1
        if t.get("localInstall"):
            types["localInstall"] += 1
        if t.get("googleDork"):
            types["googleDork"] += 1
        if t.get("registration"):
            types["registration"] += 1
        if t.get("api"):
            types["api"] += 1
        if t.get("deprecated"):
            types["deprecated"] += 1

    return {
        "totalTools": len(all_tools),
        "categories": [c for c in categories if c["depth"] == 0],
        "pricing": pricing,
        "opsec": opsec,
        "types": types,
    }


@router.get("/categories")
async def directory_categories():
    arf = _load_arf()
    categories = _get_categories(arf)
    return {"categories": [c for c in categories if c["depth"] == 0]}


@router.get("/search")
async def directory_search(q: str = Query(..., min_length=1)):
    arf = _load_arf()
    all_tools = _flatten_tools(arf)
    lower = q.lower()
    results = [
        t for t in all_tools
        if lower in t["name"].lower()
        or lower in t["description"].lower()
        or lower in t.get("bestFor", "").lower()
        or lower in t.get("input", "").lower()
        or lower in t.get("category", "").lower()
        or lower in t.get("subcategory", "").lower()
    ]
    return {"query": q, "count": len(results), "results": results[:200]}


@router.get("/category/{path:path}")
async def directory_category(path: str):
    arf = _load_arf()
    parts = [p.strip() for p in path.split("/") if p.strip()]
    node = arf
    for part in parts:
        found = None
        for child in node.get("children", []) or []:
            if child.get("name", "").lower() == part.lower():
                found = child
                break
        if found is None:
            raise HTTPException(status_code=404, detail=f"Category not found: {part}")
        node = found
    tools = _flatten_tools(node)
    subcats = _get_categories(node)
    return {
        "name": node.get("name", ""),
        "tools": tools,
        "subcategories": subcats,
        "totalTools": len(tools),
    }


@router.get("")
async def directory_full():
    arf = _load_arf()
    return arf
