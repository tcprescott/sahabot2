"""API endpoints for preset namespaces and randomizer presets."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from api.schemas.preset import (
    PresetNamespaceOut,
    PresetNamespaceListResponse,
    PresetNamespaceCreateRequest,
    PresetNamespaceUpdateRequest,
    RandomizerPresetOut,
    RandomizerPresetListResponse,
    RandomizerPresetCreateRequest,
    RandomizerPresetUpdateRequest,
)
from api.deps import get_current_user, enforce_rate_limit
from application.services.randomizer.preset_namespace_service import (
    PresetNamespaceService,
    NamespaceValidationError,
)
from application.services.randomizer.randomizer_preset_service import (
    RandomizerPresetService,
    PresetValidationError,
)
from models import User

router = APIRouter(prefix="/presets", tags=["presets"])


# ========== Preset Namespaces ==========


@router.get(
    "/namespaces",
    response_model=PresetNamespaceListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Preset Namespaces",
    description="List all preset namespaces accessible to the user.",
)
async def list_namespaces(
    current_user: User = Depends(get_current_user),
) -> PresetNamespaceListResponse:
    """
    List all preset namespaces.

    Returns namespaces owned by the current user.

    Args:
        current_user: Authenticated user

    Returns:
        PresetNamespaceListResponse: List of namespaces
    """
    service = PresetNamespaceService()
    namespaces = await service.list_user_namespaces(current_user)
    items = [PresetNamespaceOut.model_validate(ns) for ns in namespaces]
    return PresetNamespaceListResponse(items=items, count=len(items))


@router.post(
    "/namespaces",
    response_model=PresetNamespaceOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Preset Namespace",
    description="Create a new preset namespace.",
    responses={
        201: {"description": "Namespace created successfully"},
        400: {"description": "Invalid namespace data"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_namespace(
    data: PresetNamespaceCreateRequest, current_user: User = Depends(get_current_user)
) -> PresetNamespaceOut:
    """
    Create a new preset namespace.

    Args:
        data: Namespace creation data
        current_user: Authenticated user

    Returns:
        PresetNamespaceOut: Created namespace

    Raises:
        HTTPException: 400 if validation fails
    """
    service = PresetNamespaceService()
    try:
        namespace = await service.create_namespace(
            user=current_user, name=data.name, description=data.description
        )
        if not namespace:
            raise HTTPException(status_code=400, detail="Failed to create namespace")
        return PresetNamespaceOut.model_validate(namespace)
    except NamespaceValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/namespaces/{namespace_id}",
    response_model=PresetNamespaceOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Preset Namespace",
    description="Get details of a specific preset namespace.",
)
async def get_namespace(
    namespace_id: int = Path(..., description="Namespace ID"),
    current_user: User = Depends(get_current_user),
) -> PresetNamespaceOut:
    """
    Get namespace details.

    Args:
        namespace_id: ID of the namespace
        current_user: Authenticated user

    Returns:
        PresetNamespaceOut: Namespace details

    Raises:
        HTTPException: 404 if not found or not accessible
    """
    service = PresetNamespaceService()
    namespace = await service.get_namespace(namespace_id)

    if not namespace:
        raise HTTPException(status_code=404, detail="Namespace not found")

    # Check if user owns this namespace
    if namespace.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Namespace not found")

    return PresetNamespaceOut.model_validate(namespace)


@router.patch(
    "/namespaces/{namespace_id}",
    response_model=PresetNamespaceOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Preset Namespace",
    description="Update a preset namespace.",
)
async def update_namespace(
    data: PresetNamespaceUpdateRequest,
    namespace_id: int = Path(..., description="Namespace ID"),
    current_user: User = Depends(get_current_user),
) -> PresetNamespaceOut:
    """
    Update namespace.

    Args:
        data: Update data
        namespace_id: ID of the namespace
        current_user: Authenticated user

    Returns:
        PresetNamespaceOut: Updated namespace

    Raises:
        HTTPException: 404 if not found, 403 if not authorized
    """
    service = PresetNamespaceService()
    try:
        namespace = await service.update_namespace(
            user=current_user, namespace_id=namespace_id, description=data.description
        )
        if not namespace:
            raise HTTPException(
                status_code=404, detail="Namespace not found or not authorized"
            )
        return PresetNamespaceOut.model_validate(namespace)
    except NamespaceValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete(
    "/namespaces/{namespace_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Preset Namespace",
    description="Delete a preset namespace.",
    status_code=204,
)
async def delete_namespace(
    namespace_id: int = Path(..., description="Namespace ID"),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete namespace.

    Args:
        namespace_id: ID of the namespace
        current_user: Authenticated user

    Raises:
        HTTPException: 404 if not found, 403 if not authorized
    """
    service = PresetNamespaceService()
    success = await service.delete_namespace(
        user=current_user, namespace_id=namespace_id
    )
    if not success:
        raise HTTPException(
            status_code=404, detail="Namespace not found or not authorized"
        )


# ========== Randomizer Presets ==========


@router.get(
    "/",
    response_model=RandomizerPresetListResponse,
    dependencies=[Depends(enforce_rate_limit)],
    summary="List Randomizer Presets",
    description="List randomizer presets accessible to the user.",
)
async def list_presets(
    randomizer: str | None = Query(None, description="Filter by randomizer type"),
    namespace_id: int | None = Query(None, description="Filter by namespace ID"),
    include_public: bool = Query(True, description="Include public presets"),
    current_user: User = Depends(get_current_user),
) -> RandomizerPresetListResponse:
    """
    List randomizer presets.

    Returns presets owned by the user, plus public presets if include_public is True.

    Args:
        randomizer: Optional randomizer type filter
        namespace_id: Optional namespace filter
        include_public: Include public presets
        current_user: Authenticated user

    Returns:
        RandomizerPresetListResponse: List of presets
    """
    service = RandomizerPresetService()

    # Get user's presets
    user_presets = await service.list_user_presets(
        user=current_user, randomizer=randomizer, namespace_id=namespace_id
    )

    # Get public presets if requested
    public_presets = []
    if include_public:
        public_presets = await service.list_public_presets(
            randomizer=randomizer, namespace_id=namespace_id
        )

    # Combine and deduplicate
    all_presets = {p.id: p for p in user_presets + public_presets}.values()
    items = [RandomizerPresetOut.model_validate(preset) for preset in all_presets]

    return RandomizerPresetListResponse(items=items, count=len(items))


@router.post(
    "/",
    response_model=RandomizerPresetOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Create Randomizer Preset",
    description="Create a new randomizer preset.",
    responses={
        201: {"description": "Preset created successfully"},
        400: {"description": "Invalid preset data"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
    },
    status_code=201,
)
async def create_preset(
    data: RandomizerPresetCreateRequest, current_user: User = Depends(get_current_user)
) -> RandomizerPresetOut:
    """
    Create a new randomizer preset.

    Args:
        data: Preset creation data
        current_user: Authenticated user

    Returns:
        RandomizerPresetOut: Created preset

    Raises:
        HTTPException: 400 if validation fails
    """
    service = RandomizerPresetService()
    try:
        preset = await service.create_preset(
            user=current_user,
            randomizer=data.randomizer,
            name=data.name,
            yaml_content=data.settings_yaml,
            description=data.description,
            is_public=data.is_public,
            is_global=False,  # API doesn't support global presets (requires namespace)
        )
        if not preset:
            raise HTTPException(status_code=400, detail="Failed to create preset")
        return RandomizerPresetOut.model_validate(preset)
    except PresetValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/{preset_id}",
    response_model=RandomizerPresetOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Randomizer Preset",
    description="Get details of a specific randomizer preset.",
)
async def get_preset(
    preset_id: int = Path(..., description="Preset ID"),
    current_user: User = Depends(get_current_user),
) -> RandomizerPresetOut:
    """
    Get preset details.

    Args:
        preset_id: ID of the preset
        current_user: Authenticated user

    Returns:
        RandomizerPresetOut: Preset details

    Raises:
        HTTPException: 404 if not found or not accessible
    """
    service = RandomizerPresetService()
    preset = await service.get_preset(preset_id)

    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    # Check if user can access (owner or public)
    if preset.user_id != current_user.id and not preset.is_public:
        raise HTTPException(status_code=404, detail="Preset not found")

    return RandomizerPresetOut.model_validate(preset)


@router.patch(
    "/{preset_id}",
    response_model=RandomizerPresetOut,
    dependencies=[Depends(enforce_rate_limit)],
    summary="Update Randomizer Preset",
    description="Update a randomizer preset.",
)
async def update_preset(
    data: RandomizerPresetUpdateRequest,
    preset_id: int = Path(..., description="Preset ID"),
    current_user: User = Depends(get_current_user),
) -> RandomizerPresetOut:
    """
    Update preset.

    Args:
        data: Update data
        preset_id: ID of the preset
        current_user: Authenticated user

    Returns:
        RandomizerPresetOut: Updated preset

    Raises:
        HTTPException: 404 if not found, 403 if not authorized
    """
    service = RandomizerPresetService()
    try:
        preset = await service.update_preset(
            preset_id=preset_id,
            user=current_user,
            yaml_content=data.settings_yaml,
            name=data.name,
            description=data.description,
            is_public=data.is_public,
        )
        if not preset:
            raise HTTPException(
                status_code=404, detail="Preset not found or not authorized"
            )
        return RandomizerPresetOut.model_validate(preset)
    except PresetValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete(
    "/{preset_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Delete Randomizer Preset",
    description="Delete a randomizer preset.",
    status_code=204,
)
async def delete_preset(
    preset_id: int = Path(..., description="Preset ID"),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete preset.

    Args:
        preset_id: ID of the preset
        current_user: Authenticated user

    Raises:
        HTTPException: 404 if not found, 403 if not authorized
    """
    service = RandomizerPresetService()
    success = await service.delete_preset(user=current_user, preset_id=preset_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Preset not found or not authorized"
        )
