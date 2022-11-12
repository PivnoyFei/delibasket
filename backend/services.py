
async def query_list(query: list):
    return {
        "count": len(query),
        "next": None,
        "previous": None,
        "results": query
    }
