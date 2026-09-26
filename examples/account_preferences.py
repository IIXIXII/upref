"""Separate account preferences within one OS user's application configuration."""

from pathlib import Path
from tempfile import TemporaryDirectory

from upref import Config, ConfigStore


def preferences_for(store: ConfigStore, account_id: str) -> Config:
    """Resolve one account's flat preferences with application defaults."""
    accounts = store.load().get("accounts", {})
    if not isinstance(accounts, dict):
        raise ValueError("accounts must be a mapping")
    account = accounts.get(account_id, {})
    if not isinstance(account, dict):
        raise ValueError("Each account must have a preference mapping")
    resolved: Config = {"theme": "system", "language": "en"}
    resolved.update(account)
    return resolved


def main() -> None:
    """Switch accounts and change one account without replacing the other."""
    with TemporaryDirectory(prefix="upref-accounts-") as directory:
        store = ConfigStore("accounts-demo", directory=Path(directory).resolve())
        # Account IDs are mapping keys, not filesystem paths or credentials.
        store.save(
            {
                "active_account": "personal",
                "accounts": {
                    "personal": {"theme": "light"},
                    "work": {"language": "fr"},
                },
            }
        )
        store.update(
            {"active_account": "work", "accounts": {"work": {"theme": "dark"}}}
        )
        print("Work preferences:", preferences_for(store, "work"))
        print("Personal preferences unchanged:", preferences_for(store, "personal"))
        print("New account defaults:", preferences_for(store, "new-account"))
        # Signing out removes the session selection, not the user's preferences.
        saved = store.load()
        saved.pop("active_account", None)
        store.save(saved)
        print("Signed out; account preferences retained.")


if __name__ == "__main__":
    main()
