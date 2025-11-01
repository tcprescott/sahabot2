"""
Preset API routes.

REST API endpoints for preset management.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from api.deps import get_current_user, enforce_rate_limit
from api.schemas.preset import (
    PresetCreate,
    PresetUpdate,
    PresetResponse,
    PresetListResponse,
    PresetListItem,
    NamespaceListResponse,
    PresetNamespaceCreate,
    PresetNamespaceResponse,
    PresetsByRandomizerResponse,
    PresetContentResponse
)
from application.services.preset_service import PresetService
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get(
    "/namespaces",
    response_model=NamespaceListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Preset Namespaces"
)
async def list_namespaces(
    public_only: bool = True,
    current_user: Optional[User] = Depends(get_current_user)
) -> NamespaceListResponse:
    """
    List preset namespaces.

    Returns public namespaces, or public + user's private namespaces if authenticated.
    """
    service = PresetService()
    namespaces = await service.list_namespaces(public_only, current_user)

    return NamespaceListResponse(
        items=[
            PresetNamespaceResponse.model_validate(ns)
            for ns in namespaces
        ],
        count=len(namespaces)
    )


@router.post(
    "/namespaces",
    response_model=PresetNamespaceResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Preset Namespace",
    status_code=status.HTTP_201_CREATED
)
async def create_namespace(
    namespace: PresetNamespaceCreate,
    current_user: User = Depends(get_current_user)
) -> PresetNamespaceResponse:
    """
    Create a new preset namespace.

    Requires authentication.
    """
    service = PresetService()

    # Check if namespace already exists
    existing = await service.get_namespace(namespace.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Namespace already exists"
        )

    created = await service.create_namespace(
        namespace.name,
        current_user,
        namespace.is_public,
        namespace.description
    )

    return PresetNamespaceResponse.model_validate(created)


@router.get(
    "/",
    response_model=PresetListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Presets"
)
async def list_presets(
    namespace: Optional[str] = None,
    randomizer: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user)
) -> PresetListResponse:
    """
    List presets with optional filters.

    Args:
        namespace: Filter by namespace name
        randomizer: Filter by randomizer type
    """
    service = PresetService()
    presets = await service.list_presets(namespace, randomizer, current_user)

    items = [
        PresetListItem(
            id=preset.id,
            preset_name=preset.preset_name,
            randomizer=preset.randomizer,
            namespace_name=preset.namespace.name,
            description=preset.description
        )
        for preset in presets
    ]

    return PresetListResponse(items=items, count=len(items))


@router.get(
    "/{namespace}/{randomizer}/{preset_name}",
    response_model=PresetResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Preset"
)
async def get_preset(
    namespace: str,
    randomizer: str,
    preset_name: str,
    current_user: Optional[User] = Depends(get_current_user)
) -> PresetResponse:
    """
    Get a specific preset by namespace, randomizer, and name.
    """
    service = PresetService()
    preset = await service.get_preset(namespace, preset_name, randomizer)

    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preset not found"
        )

    # Check if user can access this preset
    if not preset.namespace.is_public:
        if not current_user or not await service.can_edit_namespace(current_user, preset.namespace):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preset not found"
            )

    return PresetResponse.model_validate(preset)


@router.get(
    "/{namespace}/{randomizer}/{preset_name}/content",
    response_model=PresetContentResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Preset Content as JSON"
)
async def get_preset_content(
    namespace: str,
    randomizer: str,
    preset_name: str,
    current_user: Optional[User] = Depends(get_current_user)
) -> PresetContentResponse:
    """
    Get preset content parsed as JSON (from YAML).
    """
    service = PresetService()
    preset = await service.get_preset(namespace, preset_name, randomizer)

    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preset not found"
        )

    # Check if user can access this preset
    if not preset.namespace.is_public:
        if not current_user or not await service.can_edit_namespace(current_user, preset.namespace):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preset not found"
            )

    try:
        settings = await service.get_preset_content_as_dict(preset)
    except ValueError as e:
        logger.error("Failed to parse preset %s: %s", preset.id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse preset content"
        )

    return PresetContentResponse(
        preset_name=preset.preset_name,
        randomizer=preset.randomizer,
        namespace_name=preset.namespace.name,
        settings=settings
    )


@router.post(
    "/",
    response_model=PresetResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Preset",
    status_code=status.HTTP_201_CREATED
)
async def create_preset(
    preset_data: PresetCreate,
    current_user: User = Depends(get_current_user)
) -> PresetResponse:
    """
    Create a new preset.

    Requires authentication.
    """
    service = PresetService()

    # Check if preset already exists
    existing = await service.get_preset(
        preset_data.namespace_name,
        preset_data.preset_name,
        preset_data.randomizer
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preset already exists"
        )

    try:
        preset = await service.create_preset(
            preset_data.namespace_name,
            preset_data.preset_name,
            preset_data.randomizer,
            preset_data.content,
            current_user,
            preset_data.description
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not preset:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create preset in this namespace"
        )

    return PresetResponse.model_validate(preset)


@router.put(
    "/{namespace}/{randomizer}/{preset_name}",
    response_model=PresetResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Preset"
)
async def update_preset(
    namespace: str,
    randomizer: str,
    preset_name: str,
    preset_data: PresetUpdate,
    current_user: User = Depends(get_current_user)
) -> PresetResponse:
    """
    Update an existing preset.

    Requires authentication and ownership/collaboration on the namespace.
    """
    service = PresetService()
    preset = await service.get_preset(namespace, preset_name, randomizer)

    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preset not found"
        )

    try:
        success = await service.update_preset(
            preset,
            preset_data.content,
            preset_data.description,
            current_user
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this preset"
        )

    # Fetch updated preset
    preset = await service.get_preset(namespace, preset_name, randomizer)
    return PresetResponse.model_validate(preset)


@router.delete(
    "/{namespace}/{randomizer}/{preset_name}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Preset",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_preset(
    namespace: str,
    randomizer: str,
    preset_name: str,
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a preset.

    Requires authentication and ownership/collaboration on the namespace.
    """
    service = PresetService()
    preset = await service.get_preset(namespace, preset_name, randomizer)

    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preset not found"
        )

    success = await service.delete_preset(preset, current_user)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this preset"
        )


@router.get(
    "/by-randomizer/{randomizer}",
    response_model=PresetsByRandomizerResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Presets for Randomizer"
)
async def list_presets_by_randomizer(
    randomizer: str,
    current_user: Optional[User] = Depends(get_current_user)
) -> PresetsByRandomizerResponse:
    """
    Get a structured list of presets for a specific randomizer.

    Returns presets grouped by namespace.
    """
    service = PresetService()
    presets_by_namespace = await service.list_presets_for_randomizer(
        randomizer,
        include_namespace_names=True
    )

    return PresetsByRandomizerResponse(
        randomizer=randomizer,
        presets=presets_by_namespace
    )
