
async def query_list(query: list = []):
    return {
        "count": len(query) if query else 0,
        "next": None,
        "previous": None,
        "results": query
    }
