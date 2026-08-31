from fastapi import APIRouter, Form, Header, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from esquemas import AutorActualizar, AutorCrear, LibroCrear
from dependencias import ConnectionDep

from repositorio import (
    actualizar_autor,
    crear_autor,
    crear_libro,
    eliminar_autor,
    eliminar_libro,
    obtener_autor,
    obtener_autores,
    obtener_libros,
    obtener_libros_por_autor,
)

router = APIRouter(tags=["vistas"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def bienvenida_vista(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"titulo": "¡Bienvenido a la Biblioteca de Autores y Libros!"},
    )


@router.get("/autores")
async def listar_autores(request: Request, conn: ConnectionDep):
    autores = await obtener_autores(conn)
    return templates.TemplateResponse(
        request=request,
        name="autores.html",
        context={"autores": autores},
    )


@router.post("/autores")
async def crear_autor_vista(
    request: Request,
    conn: ConnectionDep,
    nombre: str = Form(),
    pais: str | None = Form(default=None),
    nacimiento: int | None = Form(default=None),
):
    autor = AutorCrear(nombre=nombre, pais=pais, nacimiento=nacimiento)
    await crear_autor(conn, autor.nombre, autor.pais, autor.nacimiento)
    autores = await obtener_autores(conn)
    return templates.TemplateResponse(
        request=request,
        name="partials/tabla_autores.html",
        context={"autores": autores},
    )


@router.get("/autores/{autor_id}/editar")
async def editar_autor_vista(request: Request, conn: ConnectionDep, autor_id: int):
    autor = await obtener_autor(conn, autor_id)
    return templates.TemplateResponse(
        request=request,
        name="partials/fila_editar_autor.html",
        context={"autor": autor},
    )


@router.get("/autores/{autor_id}/cancelar")
async def cancelar_edicion_vista(request: Request, conn: ConnectionDep, autor_id: int):
    autor = await obtener_autor(conn, autor_id)
    return templates.TemplateResponse(
        request=request,
        name="partials/fila_autor.html",
        context={"autor": autor},
    )


@router.put("/autores/{autor_id}")
async def actualizar_autor_vista(
    request: Request,
    conn: ConnectionDep,
    autor_id: int,
    nombre: str = Form(),
    pais: str | None = Form(default=None),
    nacimiento: int | None = Form(default=None),
):
    autor = AutorActualizar(nombre=nombre, pais=pais, nacimiento=nacimiento)
    await actualizar_autor(conn, autor_id, autor.nombre, autor.pais, autor.nacimiento)
    autor_actualizado = await obtener_autor(conn, autor_id)
    return templates.TemplateResponse(
        request=request,
        name="partials/fila_autor.html",
        context={"autor": autor_actualizado},
    )


@router.delete("/autores/{autor_id}")
async def eliminar_autor_vista(request: Request, conn: ConnectionDep, autor_id: int):
    await eliminar_autor(conn, autor_id)
    autores = await obtener_autores(conn)
    return templates.TemplateResponse(
        request=request,
        name="partials/tabla_autores.html",
        context={"autores": autores},
    )


# --- Rutas de Libros e Interconexión ---

@router.get("/libros")
async def listar_libros(
    request: Request, 
    conn: ConnectionDep, 
    hx_request: str | None = Header(default=None)
):
    libros = await obtener_libros(conn)
    autores = await obtener_autores(conn)
    
    if hx_request:
        return templates.TemplateResponse(
            request=request,
            name="partials/tabla_libros.html",
            context={"libros": libros}
        )
        
    return templates.TemplateResponse(
        request=request,
        name="libros.html",
        context={"libros": libros, "autores": autores},
    )


@router.get("/autores/{autor_id}/libros")
async def ver_libros_autor(request: Request, conn: ConnectionDep, autor_id: int):
    autor = await obtener_autor(conn, autor_id)
    libros = await obtener_libros_por_autor(conn, autor_id)
    return templates.TemplateResponse(
        request=request,
        name="partials/libros_autor.html",
        context={"autor": autor, "libros": libros},
    )
    
@router.post("/libros")
async def crear_libro_vista(
    request: Request,
    conn: ConnectionDep,
    titulo: str = Form(),
    anio_publicacion: int | None = Form(default=None),
    autor_id: list[int] = Form(),
):
    libro = LibroCrear(titulo=titulo, anio_publicacion=anio_publicacion, autor_ids=autor_id)
    await crear_libro(conn, libro.titulo, libro.anio_publicacion, libro.autor_ids)
    libros = await obtener_libros(conn)
    return templates.TemplateResponse(
        request=request,
        name="partials/tabla_libros.html",
        context={"libros": libros},
    )

@router.delete("/libros/{libro_id}")
async def eliminar_libro_vista(request: Request, conn: ConnectionDep, libro_id: int):
    await eliminar_libro(conn, libro_id)
    libros = await obtener_libros(conn)
    return templates.TemplateResponse(
        request=request,
        name="partials/tabla_libros.html",
        context={"libros": libros},
    )