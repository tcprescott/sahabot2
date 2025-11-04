"""
Example: Event System Integration in Services

This file demonstrates best practices for integrating the event system
into service layer methods. These are reference examples - not meant to
be imported or executed.
"""

# Example 1: Creating an entity and emitting an event
# =====================================================

async def create_tournament(
    self,
    current_user: User,
    organization_id: int,
    name: str,
    tournament_type: str,
    **kwargs
) -> AsyncTournament:
    """Create a new tournament and emit event."""
    from application.events import EventBus, TournamentCreatedEvent

    # 1. Perform authorization check
    if not await self.can_manage_tournaments(current_user, organization_id):
        logger.warning("Unauthorized tournament creation attempt")
        return None

    # 2. Perform the database operation
    tournament = await self.repository.create(
        organization_id=organization_id,
        name=name,
        tournament_type=tournament_type,
        created_by_id=current_user.id,
        **kwargs
    )

    # 3. Emit event AFTER successful creation
    event = TournamentCreatedEvent(
        entity_id=tournament.id,
        user_id=current_user.id,
        organization_id=organization_id,
        tournament_name=name,
        tournament_type=tournament_type,
    )
    await EventBus.emit(event)
    logger.debug("Emitted TournamentCreatedEvent for tournament %s", tournament.id)

    # 4. Return the result
    return tournament


# Example 2: Updating an entity with multiple possible changes
# =============================================================

async def update_organization(
    self,
    current_user: User,
    organization_id: int,
    **updates
) -> Organization:
    """Update organization and emit event with changed fields."""
    from application.events import EventBus, OrganizationUpdatedEvent

    # 1. Authorization
    if not await self.can_manage_organization(current_user, organization_id):
        return None

    # 2. Get existing entity
    org = await self.repository.get_by_id(organization_id)
    if not org:
        raise ValueError(f"Organization {organization_id} not found")

    # 3. Track what changed (for event payload)
    changed_fields = []
    for field, value in updates.items():
        if hasattr(org, field) and getattr(org, field) != value:
            setattr(org, field, value)
            changed_fields.append(field)

    # 4. Save if anything changed
    if changed_fields:
        await org.save()

        # 5. Emit event with change details
        event = OrganizationUpdatedEvent(
            entity_id=org.id,
            user_id=current_user.id,
            organization_id=org.id,
            changed_fields=changed_fields,
        )
        await EventBus.emit(event)
        logger.debug(
            "Emitted OrganizationUpdatedEvent for org %s, changed: %s",
            org.id,
            changed_fields
        )

    return org


# Example 3: Multi-step operation with multiple events
# ====================================================

async def submit_race(
    self,
    tournament_id: int,
    permalink_id: int,
    user: User,
    time_seconds: int,
    vod_url: Optional[str] = None,
) -> AsyncTournamentRace:
    """Submit a race and emit appropriate events."""
    from application.events import EventBus, RaceSubmittedEvent

    # 1. Validate tournament and permalink exist
    tournament = await self.tournament_repo.get_by_id(tournament_id)
    if not tournament:
        raise ValueError("Tournament not found")

    permalink = await self.permalink_repo.get_by_id(permalink_id)
    if not permalink:
        raise ValueError("Permalink not found")

    # 2. Check if user is registered
    if not await self.is_user_registered(tournament_id, user.id):
        raise ValueError("User not registered for tournament")

    # 3. Create or update race submission
    existing_race = await self.repository.get_race(
        permalink_id=permalink_id,
        user_id=user.id
    )

    if existing_race:
        # Update existing submission
        existing_race.time_seconds = time_seconds
        existing_race.vod_url = vod_url
        existing_race.status = "pending_review"
        existing_race.submitted_at = datetime.now(timezone.utc)
        await existing_race.save()
        race = existing_race
    else:
        # Create new submission
        race = await self.repository.create_race(
            tournament_id=tournament_id,
            permalink_id=permalink_id,
            user_id=user.id,
            time_seconds=time_seconds,
            vod_url=vod_url,
            status="pending_review"
        )

    # 4. Emit event
    event = RaceSubmittedEvent(
        entity_id=race.id,
        user_id=user.id,
        organization_id=tournament.organization_id,
        tournament_id=tournament_id,
        permalink_id=permalink_id,
        racer_user_id=user.id,
        time_seconds=time_seconds,
        vod_url=vod_url,
    )
    await EventBus.emit(event)
    logger.info(
        "Race submitted: tournament=%s, user=%s, time=%s",
        tournament_id,
        user.id,
        time_seconds
    )

    return race


# Example 4: Cascading events (member add triggers permission init)
# =================================================================

async def add_member_to_organization(
    self,
    current_user: User,
    organization_id: int,
    user_id: int,
    initial_permissions: Optional[List[str]] = None,
) -> OrganizationMember:
    """Add member and emit events for member addition and permission grants."""
    from application.events import (
        EventBus,
        OrganizationMemberAddedEvent,
        OrganizationMemberPermissionChangedEvent
    )

    # 1. Authorization
    if not await self.can_manage_members(current_user, organization_id):
        return None

    # 2. Create membership
    member = await self.repository.create_member(
        organization_id=organization_id,
        user_id=user_id,
    )

    # 3. Emit member added event
    event = OrganizationMemberAddedEvent(
        entity_id=member.id,
        user_id=current_user.id,
        organization_id=organization_id,
        member_user_id=user_id,
        added_by_user_id=current_user.id,
    )
    await EventBus.emit(event)

    # 4. Grant initial permissions if specified
    if initial_permissions:
        for perm_name in initial_permissions:
            await self.grant_permission(
                organization_id=organization_id,
                user_id=user_id,
                permission_name=perm_name,
            )
            # Each permission grant emits its own event
            perm_event = OrganizationMemberPermissionChangedEvent(
                entity_id=member.id,
                user_id=current_user.id,
                organization_id=organization_id,
                member_user_id=user_id,
                permission_name=perm_name,
                granted=True,
            )
            await EventBus.emit(perm_event)

    logger.info(
        "Member %s added to org %s by %s with permissions: %s",
        user_id,
        organization_id,
        current_user.id,
        initial_permissions or []
    )

    return member


# Example 5: Bulk operation with batch events
# ===========================================

async def approve_all_pending_races(
    self,
    tournament_id: int,
    reviewer: User,
) -> int:
    """Approve all pending races and emit individual events."""
    from application.events import EventBus, RaceApprovedEvent

    # 1. Get tournament for auth and context
    tournament = await self.tournament_repo.get_by_id(tournament_id)
    if not tournament:
        raise ValueError("Tournament not found")

    # 2. Authorization
    if not await self.can_review_races(reviewer, tournament.organization_id):
        return 0

    # 3. Get all pending races
    pending_races = await self.repository.get_races_by_status(
        tournament_id=tournament_id,
        status="pending_review"
    )

    # 4. Approve each and emit event
    approved_count = 0
    for race in pending_races:
        race.status = "approved"
        race.reviewed_by_id = reviewer.id
        race.reviewed_at = datetime.now(timezone.utc)
        await race.save()

        # Emit individual event for each approval
        event = RaceApprovedEvent(
            entity_id=race.id,
            user_id=reviewer.id,
            organization_id=tournament.organization_id,
            tournament_id=tournament_id,
            racer_user_id=race.user_id,
            reviewer_user_id=reviewer.id,
        )
        await EventBus.emit(event)

        approved_count += 1

    logger.info(
        "Bulk approved %s races for tournament %s by reviewer %s",
        approved_count,
        tournament_id,
        reviewer.id
    )

    return approved_count


# Example 6: Error handling with events
# =====================================

async def delete_tournament(
    self,
    current_user: User,
    tournament_id: int,
    reason: Optional[str] = None,
) -> bool:
    """Delete tournament with proper error handling and event emission."""
    from application.events import EventBus, TournamentDeletedEvent

    try:
        # 1. Get tournament
        tournament = await self.repository.get_by_id(tournament_id)
        if not tournament:
            logger.warning("Tournament %s not found for deletion", tournament_id)
            return False

        # 2. Authorization
        if not await self.can_manage_tournaments(current_user, tournament.organization_id):
            logger.warning("Unauthorized deletion attempt for tournament %s", tournament_id)
            return False

        # 3. Perform deletion
        await self.repository.delete(tournament_id)

        # 4. Emit event ONLY after successful deletion
        event = TournamentDeletedEvent(
            entity_id=tournament_id,
            user_id=current_user.id,
            organization_id=tournament.organization_id,
            reason=reason,
        )
        await EventBus.emit(event)
        logger.info("Tournament %s deleted by user %s", tournament_id, current_user.id)

        return True

    except Exception as e:
        # Don't emit event if operation failed
        logger.exception("Failed to delete tournament %s: %s", tournament_id, e)
        return False


# Best Practices Summary
# ======================
# 
# 1. ✅ Emit events AFTER successful database operations
# 2. ✅ Include all context in event (user_id, organization_id, relevant data)
# 3. ✅ Log event emission at DEBUG level
# 4. ✅ Use specific event types (don't reuse generic events)
# 5. ✅ Emit one event per logical operation
# 6. ✅ Include changed_fields for update events
# 7. ✅ Set appropriate priority (use defaults unless critical)
# 8. ✅ Handle authorization before operations (events assume success)
#
# 1. ❌ Don't emit events before operations (they might fail)
# 2. ❌ Don't put business logic in event handlers
# 3. ❌ Don't query database for data that should be in event
# 4. ❌ Don't emit events in error/exception handlers
# 5. ❌ Don't block on event handling (it's async/fire-and-forget)
# 6. ❌ Don't emit events for failed operations
