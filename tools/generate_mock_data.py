#!/usr/bin/env python3
"""
Mock Data Generation Tool

Generates realistic mock data for testing purposes:
- Users (with different permission levels)
- Organizations (with members and permissions)
- Tournaments (async and scheduled)
- Matches (with players and crew)
- Async tournament data (pools, permalinks, races)

Usage:
    python tools/generate_mock_data.py --help
    python tools/generate_mock_data.py --users 50 --orgs 5 --tournaments 10
    python tools/generate_mock_data.py --preset small
    python tools/generate_mock_data.py --preset large --clear-existing
"""

import asyncio
import argparse
import logging
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tortoise import Tortoise

# Import models
from models import (
    User,
    Permission,
    Organization,
    OrganizationMember,
    OrganizationPermission,
    AsyncTournament,
    AsyncTournamentPool,
    AsyncTournamentPermalink,
    AsyncTournamentRace,
    Tournament,
    Match,
    MatchPlayers,
    MatchSeed,
    TournamentPlayers,
    Crew,
    CrewRole,
    SYSTEM_USER_ID,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Realistic test data
FIRST_NAMES = [
    "Alice",
    "Bob",
    "Charlie",
    "Diana",
    "Eve",
    "Frank",
    "Grace",
    "Henry",
    "Iris",
    "Jack",
    "Kate",
    "Leo",
    "Mia",
    "Noah",
    "Olivia",
    "Peter",
    "Quinn",
    "Rose",
    "Sam",
    "Tara",
    "Uma",
    "Victor",
    "Wendy",
    "Xander",
    "Yara",
    "Zoe",
    "Alex",
    "Blake",
    "Casey",
    "Drew",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
]

ORG_TYPES = [
    "Gaming League",
    "Racing Guild",
    "Speedrun Community",
    "Tournament Series",
    "Gaming Collective",
    "Esports Organization",
    "Racing Federation",
]

ORG_ADJECTIVES = [
    "Elite",
    "Pro",
    "Ultimate",
    "Legendary",
    "Epic",
    "Supreme",
    "Prime",
    "Mythic",
    "Grand",
    "Royal",
    "Champion",
    "Master",
    "Apex",
    "Alpha",
]

TOURNAMENT_TYPES = [
    "Championship",
    "Open",
    "Invitational",
    "Weekly",
    "Monthly",
    "Seasonal",
    "Grand Prix",
    "Cup",
    "Series",
    "League",
    "Qualifier",
    "Masters",
]

GAME_CATEGORIES = [
    "alttpr",
    "ootr",
    "smz3",
    "sm64",
    "smw",
    "smo",
    "zelda",
    "metroid",
    "pokemon",
    "ff",
    "mario",
    "sonic",
]

RACE_GOALS = [
    "Beat the game",
    "Any%",
    "100%",
    "All Dungeons",
    "Glitchless",
    "All Stars",
    "All Bosses",
    "Low%",
    "No Major Glitches",
    "Randomizer",
]


class MockDataGenerator:
    """Generates realistic mock data for testing."""

    def __init__(
        self,
        num_users: int = 20,
        num_orgs: int = 3,
        num_tournaments: int = 5,
        num_async_tournaments: int = 3,
        num_matches_per_tournament: int = 10,
        clear_existing: bool = False,
    ):
        """
        Initialize mock data generator.

        Args:
            num_users: Number of mock users to create
            num_orgs: Number of organizations to create
            num_tournaments: Number of scheduled tournaments to create
            num_async_tournaments: Number of async tournaments to create
            num_matches_per_tournament: Number of matches per tournament
            clear_existing: Whether to clear existing data before generating
        """
        self.num_users = num_users
        self.num_orgs = num_orgs
        self.num_tournaments = num_tournaments
        self.num_async_tournaments = num_async_tournaments
        self.num_matches_per_tournament = num_matches_per_tournament
        self.clear_existing = clear_existing

        # Will be populated during generation
        self.users = []
        self.orgs = []
        self.tournaments = []
        self.async_tournaments = []

    async def generate_all(self):
        """Generate all mock data."""
        logger.info("Starting mock data generation...")

        if self.clear_existing:
            await self._clear_existing_data()

        await self._generate_users()
        await self._generate_organizations()
        await self._generate_tournaments()
        await self._generate_async_tournaments()

        await self._print_summary()

        logger.info("Mock data generation complete!")

    async def _clear_existing_data(self):
        """Clear existing data from database."""
        logger.warning("Clearing existing data from database...")

        # Delete in reverse dependency order
        await MatchSeed.all().delete()
        await Crew.all().delete()
        await MatchPlayers.all().delete()
        await Match.all().delete()
        await TournamentPlayers.all().delete()
        await Tournament.all().delete()

        await AsyncTournamentRace.all().delete()
        await AsyncTournamentPermalink.all().delete()
        await AsyncTournamentPool.all().delete()
        await AsyncTournament.all().delete()

        await OrganizationMember.all().delete()
        await OrganizationPermission.all().delete()
        await Organization.all().delete()

        # Keep system user if it exists, delete others
        await User.filter(id__not=SYSTEM_USER_ID).delete()

        logger.info("Existing data cleared")

    async def _generate_users(self):
        """Generate mock users with various permission levels."""
        logger.info("Generating %s users...", self.num_users)

        # Distribution of permission levels
        # 1 SUPERADMIN, 2-3 ADMIN, ~10% MODERATOR, rest USER
        num_superadmin = 1
        num_admin = min(3, max(2, self.num_users // 20))
        num_moderator = max(1, self.num_users // 10)
        num_user = self.num_users - num_superadmin - num_admin - num_moderator

        permissions = (
            [Permission.SUPERADMIN] * num_superadmin
            + [Permission.ADMIN] * num_admin
            + [Permission.MODERATOR] * num_moderator
            + [Permission.USER] * num_user
        )
        random.shuffle(permissions)

        for i in range(self.num_users):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            username = f"{first_name}{last_name}{random.randint(1, 999)}"

            # Generate realistic Discord IDs (18-digit snowflakes)
            discord_id = random.randint(100000000000000000, 999999999999999999)

            user = await User.create(
                discord_id=discord_id,
                discord_username=username,
                discord_discriminator=str(random.randint(1, 9999)).zfill(4),
                discord_email=f"{username.lower()}@example.com",
                permission=permissions[i],
                is_active=True,
            )

            self.users.append(user)

        logger.info(
            "Created %s users: %s SUPERADMIN, %s ADMIN, %s MODERATOR, %s USER",
            len(self.users),
            num_superadmin,
            num_admin,
            num_moderator,
            num_user,
        )

    async def _generate_organizations(self):
        """Generate organizations with members and permissions."""
        logger.info("Generating %s organizations...", self.num_orgs)

        # Standard organization permissions
        org_permission_names = [
            "ADMIN",
            "TOURNAMENT_MANAGER",
            "MEMBER_MANAGER",
            "ASYNC_REVIEWER",
            "CREW_APPROVER",
            "SCHEDULED_TASK_MANAGER",
            "RACE_ROOM_MANAGER",
            "LIVE_RACE_MANAGER",
        ]

        for i in range(self.num_orgs):
            adj = random.choice(ORG_ADJECTIVES)
            org_type = random.choice(ORG_TYPES)
            name = f"{adj} {org_type} {i + 1}"

            org = await Organization.create(
                name=name,
                description=f"A {org_type.lower()} for competitive gaming and racing events.",
                is_active=True,
            )

            # Create organization permissions
            permissions = []
            for perm_name in org_permission_names:
                perm = await OrganizationPermission.create(
                    organization=org,
                    permission_name=perm_name,
                    description=f"{perm_name} permission for {name}",
                )
                permissions.append(perm)

            # Add members (30-70% of users)
            num_members = random.randint(
                int(self.num_users * 0.3), int(self.num_users * 0.7)
            )
            members_to_add = random.sample(self.users, num_members)

            for user in members_to_add:
                member = await OrganizationMember.create(organization=org, user=user)

                # Assign permissions based on user level
                if user.permission >= Permission.ADMIN:
                    # Admins get all permissions
                    await member.permissions.add(*permissions)
                elif user.permission == Permission.MODERATOR:
                    # Moderators get some permissions
                    perms_to_add = random.sample(permissions, random.randint(2, 5))
                    await member.permissions.add(*perms_to_add)
                else:
                    # Regular users might get 0-2 permissions
                    if random.random() < 0.3:  # 30% chance
                        perms_to_add = random.sample(permissions, random.randint(1, 2))
                        await member.permissions.add(*perms_to_add)

            self.orgs.append(org)

        logger.info(
            "Created %s organizations with members and permissions", len(self.orgs)
        )

    async def _generate_tournaments(self):
        """Generate scheduled tournaments with matches."""
        logger.info("Generating %s tournaments...", self.num_tournaments)

        for org in self.orgs:
            num_for_org = max(1, self.num_tournaments // len(self.orgs))

            for i in range(num_for_org):
                tournament_type = random.choice(TOURNAMENT_TYPES)
                category = random.choice(GAME_CATEGORIES)
                name = f"{org.name} - {category.upper()} {tournament_type} {i + 1}"

                tournament = await Tournament.create(
                    organization=org,
                    name=name,
                    description=f"A competitive {tournament_type.lower()} for {category}.",
                    is_active=random.random() > 0.2,  # 80% active
                    tracker_enabled=True,
                    racetime_auto_create_rooms=random.random() > 0.5,
                    room_open_minutes_before=random.choice([30, 60, 90, 120]),
                    require_racetime_link=random.random() > 0.7,
                    racetime_default_goal=random.choice(RACE_GOALS),
                )

                # Add tournament players (subset of org members)
                org_members = (
                    await OrganizationMember.filter(organization=org)
                    .prefetch_related("user")
                    .all()
                )

                num_players = min(len(org_members), random.randint(4, 20))
                players = random.sample(org_members, num_players)

                for member in players:
                    await TournamentPlayers.create(
                        tournament=tournament, user=member.user
                    )

                # Generate matches
                await self._generate_matches(tournament, players)

                self.tournaments.append(tournament)

        logger.info("Created %s tournaments with matches", len(self.tournaments))

    async def _generate_matches(self, tournament: Tournament, players: list):
        """Generate matches for a tournament."""
        # Need at least 2 players for matches
        if len(players) < 2:
            logger.warning(
                "Not enough players for matches in tournament %s", tournament.name
            )
            return

        num_matches = self.num_matches_per_tournament

        for i in range(num_matches):
            # Schedule matches across next 30 days
            scheduled_at = datetime.now(timezone.utc) + timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.choice([0, 15, 30, 45]),
            )

            # Some matches are in the past (for testing completed states)
            if random.random() < 0.3:
                scheduled_at = datetime.now(timezone.utc) - timedelta(
                    days=random.randint(1, 60)
                )

            match = await Match.create(
                tournament=tournament,
                scheduled_at=scheduled_at,
                title=f"Match {i + 1}",
                racetime_goal=tournament.racetime_default_goal,
                racetime_invitational=True,
                racetime_auto_create=tournament.racetime_auto_create_rooms,
            )

            # Add 2-4 players to match (but not more than available)
            max_players = min(4, len(players))
            num_match_players = random.randint(2, max_players)
            match_players = random.sample(players, num_match_players)

            for j, player_member in enumerate(match_players):
                await MatchPlayers.create(
                    match=match,
                    user=player_member.user,
                    finish_rank=None,  # Not finished yet
                    assigned_station=f"Station {j + 1}",
                )

            # Some matches are completed (past matches)
            if scheduled_at < datetime.now(timezone.utc):
                # Set match as started and finished
                match.started_at = scheduled_at + timedelta(
                    minutes=random.randint(5, 15)
                )
                match.finished_at = match.started_at + timedelta(
                    minutes=random.randint(30, 180)
                )

                # Assign finish ranks
                players_list = await MatchPlayers.filter(match=match).all()
                random.shuffle(players_list)
                for rank, player in enumerate(players_list, start=1):
                    player.finish_rank = rank
                    await player.save()

                # Maybe add seed
                if random.random() > 0.3:
                    await MatchSeed.create(
                        match=match,
                        url=f"https://example.com/seed/{random.randint(100000, 999999)}",
                        description="Randomizer seed for this match",
                    )

                await match.save()

            # Add crew members (commentators, trackers)
            if random.random() > 0.5:
                num_crew = random.randint(1, 3)
                available_users = [p for p in players if p not in match_players]
                if available_users:
                    crew_members = random.sample(
                        available_users, min(num_crew, len(available_users))
                    )
                    for crew_member in crew_members:
                        await Crew.create(
                            match=match,
                            user=crew_member.user,
                            role=random.choice(list(CrewRole)),
                        )

    async def _generate_async_tournaments(self):
        """Generate async tournaments with pools, permalinks, and races."""
        logger.info("Generating %s async tournaments...", self.num_async_tournaments)

        for org in self.orgs:
            num_for_org = max(1, self.num_async_tournaments // len(self.orgs))

            for i in range(num_for_org):
                category = random.choice(GAME_CATEGORIES)
                name = f"{org.name} - Async {category.upper()} {i + 1}"

                async_tournament = await AsyncTournament.create(
                    organization=org,
                    name=name,
                    description=f"Asynchronous racing tournament for {category}.",
                    is_active=random.random() > 0.2,
                    hide_results=random.random() > 0.6,
                    runs_per_pool=random.randint(1, 3),
                )

                # Generate 2-5 pools
                num_pools = random.randint(2, 5)
                for pool_idx in range(num_pools):
                    pool = await AsyncTournamentPool.create(
                        tournament=async_tournament,
                        name=f"Pool {pool_idx + 1}",
                        description=f"Collection of seeds for pool {pool_idx + 1}",
                    )

                    # Generate 3-8 permalinks per pool
                    num_permalinks = random.randint(3, 8)
                    for perm_idx in range(num_permalinks):
                        permalink = await AsyncTournamentPermalink.create(
                            pool=pool,
                            url=f"https://alttpr.com/h/{self._random_hash()}",
                            notes=f"Seed {perm_idx + 1} for {pool.name}",
                        )

                        # Generate races for some permalinks
                        org_members = (
                            await OrganizationMember.filter(organization=org)
                            .prefetch_related("user")
                            .all()
                        )

                        num_racers = random.randint(0, min(10, len(org_members)))
                        racers = random.sample(org_members, num_racers)

                        for racer in racers:
                            # Some races are completed, some are in progress
                            # Status values: 'pending', 'in_progress', 'finished', 'forfeit', 'disqualified'
                            # Review status values: 'pending', 'accepted', 'rejected'
                            status = random.choice(
                                ["finished", "finished", "in_progress", "pending"]
                            )

                            review_status = "pending"
                            if status == "finished":
                                review_status = random.choice(
                                    ["pending", "accepted", "rejected"]
                                )

                            if status == "finished" and review_status == "accepted":
                                # Completed and accepted races have times
                                start_time = datetime.now(timezone.utc) - timedelta(
                                    days=random.randint(1, 30)
                                )
                                elapsed = timedelta(
                                    hours=random.randint(1, 3),
                                    minutes=random.randint(0, 59),
                                    seconds=random.randint(0, 59),
                                )
                                end_time = start_time + elapsed
                                vod_url = f"https://twitch.tv/videos/{random.randint(1000000000, 9999999999)}"
                            else:
                                start_time = None
                                end_time = None
                                vod_url = None

                            await AsyncTournamentRace.create(
                                tournament=async_tournament,
                                permalink=permalink,
                                user=racer.user,
                                status=status,
                                review_status=review_status,
                                start_time=start_time,
                                end_time=end_time,
                                runner_vod_url=vod_url,
                                runner_notes=(
                                    f"Race by {racer.user.discord_username}"
                                    if random.random() > 0.5
                                    else None
                                ),
                            )

                self.async_tournaments.append(async_tournament)

        logger.info(
            "Created %s async tournaments with pools and races",
            len(self.async_tournaments),
        )

    def _random_hash(self) -> str:
        """Generate random hash string for permalinks."""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(random.choice(chars) for _ in range(10))

    def _random_seed_code(self) -> str:
        """Generate random seed code."""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(random.choice(chars) for _ in range(8))

    async def _print_summary(self):
        """Print summary of generated data."""
        print("\n" + "=" * 60)
        print("MOCK DATA GENERATION SUMMARY")
        print("=" * 60)

        # Users
        total_users = await User.all().count()
        superadmins = await User.filter(permission=Permission.SUPERADMIN).count()
        admins = await User.filter(permission=Permission.ADMIN).count()
        moderators = await User.filter(permission=Permission.MODERATOR).count()
        regular_users = await User.filter(permission=Permission.USER).count()

        print(f"\nUSERS: {total_users} total")
        print(f"  - SUPERADMIN: {superadmins}")
        print(f"  - ADMIN: {admins}")
        print(f"  - MODERATOR: {moderators}")
        print(f"  - USER: {regular_users}")

        # Organizations
        total_orgs = await Organization.all().count()
        total_members = await OrganizationMember.all().count()
        total_org_perms = await OrganizationPermission.all().count()

        print(f"\nORGANIZATIONS: {total_orgs} total")
        print(f"  - Total memberships: {total_members}")
        print(f"  - Total permissions: {total_org_perms}")

        # Tournaments
        total_tournaments = await Tournament.all().count()
        active_tournaments = await Tournament.filter(is_active=True).count()
        total_matches = await Match.all().count()
        completed_matches = await Match.filter(finished_at__not_isnull=True).count()

        print(f"\nTOURNAMENTS: {total_tournaments} total ({active_tournaments} active)")
        print(f"  - Total matches: {total_matches}")
        print(f"  - Completed matches: {completed_matches}")

        # Async Tournaments
        total_async = await AsyncTournament.all().count()
        active_async = await AsyncTournament.filter(is_active=True).count()
        total_pools = await AsyncTournamentPool.all().count()
        total_permalinks = await AsyncTournamentPermalink.all().count()
        total_races = await AsyncTournamentRace.all().count()
        approved_races = await AsyncTournamentRace.filter(
            review_status="accepted"
        ).count()

        print(f"\nASYNC TOURNAMENTS: {total_async} total ({active_async} active)")
        print(f"  - Total pools: {total_pools}")
        print(f"  - Total permalinks: {total_permalinks}")
        print(f"  - Total races: {total_races}")
        print(f"  - Approved races: {approved_races}")

        print("\n" + "=" * 60)

        # Sample login credentials
        print("\nSAMPLE USERS (for testing):")
        print("-" * 60)
        sample_users = await User.all().limit(5)
        for user in sample_users:
            print(f"  {user.discord_username} ({user.permission.name})")
            print(f"    Discord ID: {user.discord_id}")
            print(f"    Email: {user.discord_email}")

        print("\n" + "=" * 60 + "\n")


async def init_db():
    """Initialize database connection."""
    from config import settings

    await Tortoise.init(
        db_url=settings.database_url,
        modules={
            "models": [
                "models.user",
                "models.organizations",
                "models.async_tournament",
                "models.match_schedule",
                "models.audit_log",
                "models.api_token",
                "models.organization_invite",
                "models.organization_request",
                "models.racer_verification",
                "models.preset_namespace",
                "models.preset_namespace_permission",
                "models.randomizer_preset",
                "models.race_room_profile",
                "models.racetime_bot",
                "models.racetime_chat_command",
                "models.scheduled_task",
                "models.settings",
                "models.tournament_usage",
                "models.notification_subscription",
                "models.notification_log",
                "models.discord_guild",
                "models.discord_scheduled_event",
                "models.organization_feature_flag",
            ]
        },
    )
    await Tortoise.generate_schemas()


async def close_db():
    """Close database connections."""
    await Tortoise.close_connections()


# Preset configurations
PRESETS = {
    "tiny": {
        "num_users": 5,
        "num_orgs": 1,
        "num_tournaments": 1,
        "num_async_tournaments": 1,
        "num_matches_per_tournament": 3,
    },
    "small": {
        "num_users": 20,
        "num_orgs": 3,
        "num_tournaments": 5,
        "num_async_tournaments": 3,
        "num_matches_per_tournament": 10,
    },
    "medium": {
        "num_users": 50,
        "num_orgs": 5,
        "num_tournaments": 10,
        "num_async_tournaments": 5,
        "num_matches_per_tournament": 15,
    },
    "large": {
        "num_users": 100,
        "num_orgs": 10,
        "num_tournaments": 20,
        "num_async_tournaments": 10,
        "num_matches_per_tournament": 20,
    },
}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate mock data for testing SahaBot2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use small preset
  python tools/generate_mock_data.py --preset small

  # Custom configuration
  python tools/generate_mock_data.py --users 50 --orgs 5 --tournaments 10

  # Clear existing data and use large preset
  python tools/generate_mock_data.py --preset large --clear-existing

Available presets:
  tiny   - 5 users, 1 org, minimal data (quick testing)
  small  - 20 users, 3 orgs, moderate data (default)
  medium - 50 users, 5 orgs, substantial data
  large  - 100 users, 10 orgs, extensive data (stress testing)
        """,
    )

    parser.add_argument(
        "--preset",
        choices=["tiny", "small", "medium", "large"],
        help="Use preset configuration",
    )
    parser.add_argument("--users", type=int, help="Number of users to generate")
    parser.add_argument("--orgs", type=int, help="Number of organizations to generate")
    parser.add_argument(
        "--tournaments", type=int, help="Number of scheduled tournaments to generate"
    )
    parser.add_argument(
        "--async-tournaments", type=int, help="Number of async tournaments to generate"
    )
    parser.add_argument("--matches", type=int, help="Number of matches per tournament")
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Clear existing data before generating (WARNING: destructive!)",
    )

    args = parser.parse_args()

    # Determine configuration
    if args.preset:
        config = PRESETS[args.preset]
    else:
        config = PRESETS["small"]  # Default

    # Override with command-line arguments
    if args.users is not None:
        config["num_users"] = args.users
    if args.orgs is not None:
        config["num_orgs"] = args.orgs
    if args.tournaments is not None:
        config["num_tournaments"] = args.tournaments
    if args.async_tournaments is not None:
        config["num_async_tournaments"] = args.async_tournaments
    if args.matches is not None:
        config["num_matches_per_tournament"] = args.matches

    # Warning for clear-existing
    if args.clear_existing:
        print("\n" + "!" * 60)
        print("WARNING: This will DELETE ALL EXISTING DATA!")
        print("!" * 60)
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return

    # Run generator
    async def run():
        await init_db()
        try:
            generator = MockDataGenerator(
                num_users=config["num_users"],
                num_orgs=config["num_orgs"],
                num_tournaments=config["num_tournaments"],
                num_async_tournaments=config["num_async_tournaments"],
                num_matches_per_tournament=config["num_matches_per_tournament"],
                clear_existing=args.clear_existing,
            )
            await generator.generate_all()
        finally:
            await close_db()

    asyncio.run(run())


if __name__ == "__main__":
    main()
