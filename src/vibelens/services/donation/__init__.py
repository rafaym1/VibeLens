"""Donation services for sending and receiving session data."""

# Receiver-side append-only log: incoming donations from self-use instances.
INDEX_FILENAME = "index.jsonl"
# Sender-side append-only log: donations made from this machine/browser.
SENDER_INDEX_FILENAME = "sent.jsonl"
