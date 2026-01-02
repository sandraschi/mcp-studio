import asyncio
from mcp_studio.tools.landing_page_builder import create_landing_page
import os


async def main():
    print("Testing Landing Page Builder...")

    result = await create_landing_page(
        project_name="Vortex AI",
        hero_title="Reasoning at Speed",
        hero_subtitle="The world's fastest reasoning engine for complex tasks.",
        features=[
            "Hyper-Fast: Results in milliseconds.",
            "Deep Thought: Solves graduate-level physics.",
            "Secure: Local-first architecture.",
        ],
        target_path="d:/Dev/tmp/test_sites",
        author_name="Sandra Schipal",
        author_bio="Vienna-based reductionist building the future.",
        donate_link="https://patreon.com/example",
    )

    print(result)

    # Verify files exist
    base_path = "d:/Dev/tmp/test_sites/vortex-ai/www"
    expected_files = [
        "index.html",
        "bio.html",
        "download.html",
        "donate.html",
        "how_it_works.html",
        "styles.css",
    ]

    for f in expected_files:
        path = os.path.join(base_path, f)
        if os.path.exists(path):
            print(f"[OK] {f} exists")
        else:
            print(f"[FAIL] {f} missing")


if __name__ == "__main__":
    asyncio.run(main())
