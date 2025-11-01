"""
Bingosync service for generating bingo cards.

This service handles creation of Bingosync rooms and bingo card generation.
"""

import logging
from typing import Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup
from .randomizer_service import RandomizerResult

logger = logging.getLogger(__name__)


class BingosyncService:
    """
    Service for Bingosync integration.

    Creates and manages Bingosync rooms for various games.

    WARNING: This uses private Bingosync endpoints that are not intended
    for public consumption. This could break at any time.
    """

    BASE_URL = 'https://bingosync.com'

    def __init__(self, nickname: str = "SahaBot2"):
        """
        Initialize the Bingosync service.

        Args:
            nickname: Nickname to use when creating rooms (default: SahaBot2)
        """
        self.nickname = nickname
        self.cookies = {}

    async def generate(
        self,
        room_name: str,
        passphrase: str,
        game_type: str,
        variant_type: Optional[str] = None,
        lockout_mode: str = '1',
        seed: str = '',
        custom_json: str = '',
        is_spectator: str = 'on',
        hide_card: str = 'on'
    ) -> RandomizerResult:
        """
        Create a new Bingosync room.

        Args:
            room_name: Name for the bingo room
            passphrase: Password for the room
            game_type: Type of game for bingo generation
            variant_type: Optional variant type for the game
            lockout_mode: Lockout mode ('1', '2', or '3')
            seed: Optional seed for card generation
            custom_json: Optional custom JSON for goals
            is_spectator: Whether creator is spectator ('on' or 'off')
            hide_card: Whether to hide card ('on' or 'off')

        Returns:
            RandomizerResult: Room information

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If room creation fails
        """
        # Get CSRF token
        csrf_token = await self._get_csrf_token()

        # Prepare form data
        data = {
            'csrfmiddlewaretoken': csrf_token,
            'nickname': self.nickname,
            'room_name': room_name,
            'passphrase': passphrase,
            'game_type': game_type,
            'lockout_mode': lockout_mode,
            'seed': seed,
            'custom_json': custom_json,
            'is_spectator': is_spectator,
            'hide_card': hide_card
        }

        if variant_type is not None:
            data['variant_type'] = variant_type

        logger.info("Creating Bingosync room: %s", room_name)

        async with httpx.AsyncClient(cookies=self.cookies, follow_redirects=False) as client:
            response = await client.post(
                self.BASE_URL,
                data=data,
                headers={
                    'Origin': self.BASE_URL,
                    'Referer': self.BASE_URL
                }
            )

            # Store cookies for future requests
            self.cookies.update(response.cookies)

            if response.status_code == 302:
                room_id = response.headers['Location'].split("/")[-1]
                room_url = f"{self.BASE_URL}/room/{room_id}"

                logger.info("Created Bingosync room %s", room_id)

                return RandomizerResult(
                    url=room_url,
                    hash_id=room_id,
                    settings={
                        'game_type': game_type,
                        'variant_type': variant_type,
                        'seed': seed,
                        'lockout_mode': lockout_mode
                    },
                    randomizer='bingosync',
                    permalink=room_url,
                    metadata={
                        'room_id': room_id,
                        'password': passphrase,
                        'room_name': room_name
                    }
                )
            else:
                raise ValueError("Failed to create Bingosync room")

    async def new_card(
        self,
        room_id: str,
        game_type: str,
        variant_type: Optional[str] = None,
        lockout_mode: str = '1',
        seed: str = '',
        custom_json: str = '',
        hide_card: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a new card for an existing room.

        Args:
            room_id: ID of the room
            game_type: Type of game for bingo generation
            variant_type: Optional variant type for the game
            lockout_mode: Lockout mode ('1', '2', or '3')
            seed: Optional seed for card generation
            custom_json: Optional custom JSON for goals
            hide_card: Whether to hide the card

        Returns:
            dict: API response

        Raises:
            httpx.HTTPError: If the request fails
        """
        data = {
            'hide_card': hide_card,
            'game_type': game_type,
            'custom_json': custom_json,
            'lockout_mode': lockout_mode,
            'seed': seed,
            'room': room_id
        }

        if variant_type is not None:
            data['variant_type'] = variant_type

        async with httpx.AsyncClient(cookies=self.cookies) as client:
            response = await client.put(
                f"{self.BASE_URL}/api/new-card",
                json=data
            )
            response.raise_for_status()
            return response.json()

    async def _get_csrf_token(self) -> str:
        """
        Get CSRF token from Bingosync.

        Returns:
            str: CSRF token

        Raises:
            ValueError: If CSRF token cannot be found
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, features="html.parser")
            csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})

            if not csrf_input:
                raise ValueError("Could not find CSRF token")

            # Store cookies for subsequent requests
            self.cookies.update(response.cookies)

            return csrf_input.get('value')
