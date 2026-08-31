import json

from loguru import logger


async def obtener_autores(conn) -> list[dict]:
    rows = await conn.fetch("SELECT * FROM autores ORDER BY id")
    return [dict(row) for row in rows]


async def obtener_autor(conn, autor_id: int) -> dict | None:
    row = await conn.fetchrow("SELECT * FROM autores WHERE id = $1", autor_id)
    return dict(row) if row else None


async def crear_autor(conn, nombre: str, pais: str | None, nacimiento: int | None) -> dict:
    row = await conn.fetchrow(
        "INSERT INTO autores (nombre, pais, nacimiento) VALUES ($1, $2, $3) RETURNING *",
        nombre,
        pais,
        nacimiento,
    )
    return dict(row)


async def actualizar_autor(
    conn, autor_id: int, nombre: str, pais: str | None, nacimiento: int | None
) -> dict | None:
    row = await conn.fetchrow(
        "UPDATE autores SET nombre = $1, pais = $2, nacimiento = $3 WHERE id = $4 RETURNING *",
        nombre,
        pais,
        nacimiento,
        autor_id,
    )
    return dict(row) if row else None


async def eliminar_autor(conn, autor_id: int) -> bool:
    result = await conn.execute("DELETE FROM autores WHERE id = $1", autor_id)
    return result == "DELETE 1"


# --- Funciones para Libros ---

async def obtener_libros(conn) -> list[dict]:
    rows = await conn.fetch("""
        SELECT
            l.id,
            l.titulo,
            l.anio_publicacion,
            COALESCE(
                json_agg(
                    json_build_object('id', a.id, 'nombre', a.nombre)
                    ORDER BY a.nombre
                ) FILTER (WHERE a.id IS NOT NULL),
                '[]'
            ) AS autores
        FROM libros l
        LEFT JOIN autor_libro al ON al.libro_id = l.id
        LEFT JOIN autores a ON a.id = al.autor_id
        GROUP BY l.id, l.titulo, l.anio_publicacion
        ORDER BY l.id
    """)
    resultado = []
    for row in rows:
        d = dict(row)
        d["autores"] = json.loads(d["autores"])
        resultado.append(d)
    return resultado


async def obtener_libros_por_autor(conn, autor_id: int) -> list[dict]:
    rows = await conn.fetch("""
        SELECT l.id, l.titulo, l.anio_publicacion
        FROM libros l
        JOIN autor_libro al ON al.libro_id = l.id
        WHERE al.autor_id = $1
        ORDER BY l.id
    """, autor_id)
    return [dict(row) for row in rows]


async def crear_libro(conn, titulo: str, anio_publicacion: int | None, autor_ids: list[int]) -> dict:
    async with conn.transaction():
        libro_row = await conn.fetchrow(
            "INSERT INTO libros (titulo, anio_publicacion) VALUES ($1, $2) RETURNING id, titulo, anio_publicacion",
            titulo, anio_publicacion,
        )
        libro_id = libro_row["id"]
        autores_rows = await conn.fetch(
            "SELECT id, nombre FROM autores WHERE id = ANY($1::int[]) ORDER BY nombre",
            autor_ids,
        )
        for autor_id in autor_ids:
            await conn.execute(
                "INSERT INTO autor_libro (autor_id, libro_id) VALUES ($1, $2)",
                autor_id, libro_id,
            )
    libro_dict = dict(libro_row)
    libro_dict["autores"] = [dict(r) for r in autores_rows]
    return libro_dict


async def eliminar_libro(conn, libro_id: int) -> bool:
    result = await conn.execute("DELETE FROM libros WHERE id = $1", libro_id)
    return result == "DELETE 1"


async def upsert_autores_bulk(
    conn, registros: list[dict], *, tabla: str = "autores"
) -> int:
    if not tabla.replace("_", "").isalnum():
        raise ValueError(f"Nombre de tabla inválido: {tabla!r}")
    sql = f"""
        INSERT INTO {tabla} (id, nombre, pais, nacimiento)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (id) DO UPDATE
        SET nombre = EXCLUDED.nombre,
            pais = EXCLUDED.pais,
            nacimiento = EXCLUDED.nacimiento
    """
    count = 0
    async with conn.transaction():
        for r in registros:
            await conn.execute(
                sql,
                r["id"],
                r["nombre"],
                r.get("pais"),
                r.get("nacimiento"),
            )
            count += 1
    return count