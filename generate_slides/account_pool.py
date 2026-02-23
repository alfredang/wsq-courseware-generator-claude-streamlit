"""
Account Pool Manager for NotebookLM multi-account slide generation.

Manages multiple Google accounts, each limited to N decks per generation session.
Handles client creation and deck distribution.

Credentials loaded from environment variables:
  NOTEBOOKLM_EMAILS          - comma-separated list of emails
  NOTEBOOKLM_PASSWORD        - shared password
  NOTEBOOKLM_MAX_DECKS_PER_ACCOUNT - max decks per account (default 3)
"""

import math
import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AccountInfo:
    """Represents a single NotebookLM Google account."""
    email: str
    password: str
    account_key: str
    storage_dir: Path
    storage_state_path: Path
    is_authenticated: bool = False
    decks_assigned: int = 0
    decks_completed: int = 0
    decks_failed: int = 0
    error: Optional[str] = None


class AccountPool:
    """
    Pool manager for NotebookLM Google accounts.

    Loads account credentials from env vars, manages per-account storage states,
    and distributes decks across accounts with a configurable per-account limit.
    """

    def __init__(self):
        self.max_decks_per_account = int(
            os.environ.get("NOTEBOOKLM_MAX_DECKS_PER_ACCOUNT", "3")
        )
        self.accounts: List[AccountInfo] = []
        self._base_dir = Path.home() / ".notebooklm" / "accounts"
        self._load_accounts()

    def _load_accounts(self):
        """Load account list from environment variables."""
        emails_str = os.environ.get("NOTEBOOKLM_EMAILS", "")
        password = os.environ.get("NOTEBOOKLM_PASSWORD", "")

        if not emails_str:
            logger.warning("NOTEBOOKLM_EMAILS not set in environment.")
            return

        emails = [e.strip() for e in emails_str.split(",") if e.strip()]

        for email in emails:
            key = email.split("@")[0].replace(".", "_")
            storage_dir = self._base_dir / key
            storage_state_path = storage_dir / "storage_state.json"

            self.accounts.append(AccountInfo(
                email=email,
                password=password,
                account_key=key,
                storage_dir=storage_dir,
                storage_state_path=storage_state_path,
                is_authenticated=storage_state_path.exists(),
            ))

    def get_authenticated(self) -> List[AccountInfo]:
        """Return accounts that have valid storage_state.json files."""
        return [a for a in self.accounts if a.is_authenticated]

    def get_unauthenticated(self) -> List[AccountInfo]:
        """Return accounts needing authentication."""
        return [a for a in self.accounts if not a.is_authenticated]

    def accounts_needed(self, num_decks: int) -> int:
        """Calculate how many accounts are needed for a given number of decks."""
        return math.ceil(num_decks / self.max_decks_per_account)

    def distribute_decks(self, chunks: list) -> List[Tuple[AccountInfo, list]]:
        """
        Distribute deck chunks across available authenticated accounts.

        Returns list of (AccountInfo, [chunk_list]) tuples.
        Raises ValueError if not enough authenticated accounts.
        """
        num_decks = len(chunks)
        needed = self.accounts_needed(num_decks)
        available = self.get_authenticated()

        if len(available) < needed:
            raise ValueError(
                f"Need {needed} authenticated accounts for {num_decks} decks "
                f"(max {self.max_decks_per_account}/account), "
                f"but only {len(available)} authenticated. "
                f"Run: python -m generate_slides.authenticate_accounts"
            )

        assignments = []
        chunk_idx = 0
        for i in range(needed):
            account = available[i]
            end = min(chunk_idx + self.max_decks_per_account, num_decks)
            assigned_chunks = chunks[chunk_idx:end]
            account.decks_assigned = len(assigned_chunks)
            assignments.append((account, assigned_chunks))
            chunk_idx = end

        return assignments

    def get_status(self) -> dict:
        """Return a summary of all account statuses for UI display."""
        return {
            "total": len(self.accounts),
            "authenticated": len(self.get_authenticated()),
            "unauthenticated": len(self.get_unauthenticated()),
            "max_decks_per_account": self.max_decks_per_account,
            "accounts": [
                {
                    "email": a.email,
                    "authenticated": a.is_authenticated,
                    "decks_assigned": a.decks_assigned,
                    "decks_completed": a.decks_completed,
                    "decks_failed": a.decks_failed,
                    "error": a.error,
                }
                for a in self.accounts
            ],
        }
