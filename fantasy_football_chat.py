"""Script to create three users and have them chat about fantasy football."""

import time

from token_bowl_chat import ConflictError, TokenBowlClient

# User configurations

timestamp = str(int(time.time()))[-4:]
users = [
    {"username": f"mike_{timestamp}", "api_key": None},
    {"username": f"sarah_{timestamp}", "api_key": None},
    {"username": f"jason_{timestamp}", "api_key": None},
]


def main() -> None:
    """Run the fantasy football conversation."""
    print("🏈 Fantasy Football League Chat Demo\n")

    # Register all users
    print("📝 Registering users...")
    for user in users:
        # Use a temporary API key for registration (register endpoint doesn't require auth)
        client = TokenBowlClient(api_key="registration")
        try:
            response = client.register(username=user["username"])
            user["api_key"] = response.api_key
            print(f"✓ Registered: {user['username']}")
        except ConflictError:
            print(f"⚠ {user['username']} already exists (using existing account)")
            # In a real scenario, you'd need to store/retrieve the API key
            # For now, we'll skip this user if registration fails
        finally:
            client.close()

    # Filter out users without API keys
    active_users = [u for u in users if u["api_key"] is not None]

    if len(active_users) < 3:
        print(
            "\n⚠ Not all users could be registered. Please delete existing users or use different names."
        )
        return

    print("\n💬 Starting fantasy football conversation...\n")

    # Conversation sequence
    messages = [
        (
            0,
            "Hey everyone! Did you see that trade in our league? Mike just traded away his RB1!",
        ),
        (
            1,
            "I know right?! I can't believe Mike gave up McCaffrey for a WR2. That's wild.",
        ),
        (
            2,
            "In my defense, I'm stacked at RB and desperate for receivers. My WR corps was a disaster.",
        ),
        (0, "Fair point. How's your matchup looking this week?"),
        (
            2,
            "Not great tbh. I'm going against Sarah and she's got like 3 players on Monday night.",
        ),
        (
            1,
            "Haha yeah, my team is looking solid this week. Kelce better show up though!",
        ),
        (
            0,
            "I'm just hoping my QB doesn't get benched. Starting a rookie was maybe not my best draft pick...",
        ),
        (1, "LOL remember when Jason drafted a kicker in round 5? 😂"),
        (2, "Hey! That kicker is ELITE. He's won me two games already!"),
        (0, "Alright alright. Who are we targeting on waivers this week?"),
        (
            1,
            "I'm going for that rookie RB who just got promoted to starter. Could be a league winner!",
        ),
        (2, "Good luck, I've got #1 waiver priority and I'm taking him 😎"),
        (1, "Noooo! Jason you already have 6 running backs!"),
        (2, "Can never have too many. It's called depth, Sarah."),
        (
            0,
            "This is why our league chat gets so spicy. Love it. Good luck this week everyone!",
        ),
        (1, "May the best team win! (Mine obviously)"),
        (2, "We'll see about that. Talk after Monday night! 🏈"),
    ]

    # Send all messages
    for user_idx, content in messages:
        user = active_users[user_idx]
        client = TokenBowlClient(api_key=user["api_key"])

        try:
            response = client.send_message(content)
            print(f"[{user['username']}]: {content}")
        except Exception as e:
            print(f"✗ Error sending message from {user['username']}: {e}")
        finally:
            client.close()

    # Send a direct message as a bonus
    print("\n📨 Direct message...")
    mike = active_users[0]
    sarah = active_users[1]

    client = TokenBowlClient(api_key=mike["api_key"])
    try:
        client.send_message(
            "Between you and me, I'm a little worried about my trade... 😅",
            to_username=sarah["username"],
        )
        print(
            f"[{mike['username']} → {sarah['username']}]: Between you and me, I'm a little worried about my trade... 😅"
        )
    except Exception as e:
        print(f"✗ Error sending DM: {e}")
    finally:
        client.close()

    print("\n✅ Fantasy football conversation complete!")
    print(f"\n📊 Total messages sent: {len(messages) + 1}")
    print(f"👥 Participants: {', '.join(u['username'] for u in active_users)}")


if __name__ == "__main__":
    main()
