from dataclasses import dataclass

from social_agent.models.context import CommitContext


@dataclass
class EvalCase:
    name: str
    context: CommitContext
    expect_prefilter_skip: bool
    expected_change_type: str | None = None
    expected_worthiness_min: int | None = None
    expected_worthiness_max: int | None = None


CASES: list[EvalCase] = [
    EvalCase(
        name="lockfile_only",
        context=CommitContext(
            repo_name="demo", commit_sha="a1", commit_message="chore: bump deps",
            author="dev", changed_files=["package-lock.json"],
            diff="diff --git a/package-lock.json b/package-lock.json\n... lockfile changes ...",
        ),
        expect_prefilter_skip=True,
    ),
    EvalCase(
        name="typo_fix",
        context=CommitContext(
            repo_name="demo", commit_sha="a2", commit_message="fix: typo in README",
            author="dev", changed_files=["README.md"],
            diff="diff --git a/README.md b/README.md\n@@ -1 +1 @@\n-Helo\n+Hello",
        ),
        expect_prefilter_skip=True,
    ),
    EvalCase(
        name="real_feature_auth",
        context=CommitContext(
            repo_name="demo", commit_sha="a3", commit_message="feat: add JWT authentication middleware",
            author="dev", changed_files=["src/auth.py"],
            diff=(
                "diff --git a/src/auth.py b/src/auth.py\nnew file mode 100644\n"
                "--- /dev/null\n+++ b/src/auth.py\n@@ -0,0 +1,7 @@\n"
                "+import jwt\n+\n+def create_token(user_id, secret):\n"
                "+    return jwt.encode({'sub': user_id}, secret, algorithm='HS256')\n+\n"
                "+def verify_token(token, secret):\n"
                "+    return jwt.decode(token, secret, algorithms=['HS256'])\n"
            ),
        ),
        expect_prefilter_skip=False,
        expected_change_type="feature",
        expected_worthiness_min=60,
    ),
    EvalCase(
        name="real_bugfix_race_condition",
        context=CommitContext(
            repo_name="demo", commit_sha="a4",
            commit_message="fix: prevent race condition in payment webhook handler",
            author="dev", changed_files=["src/webhooks/payment.py"],
            diff=(
                "diff --git a/src/webhooks/payment.py b/src/webhooks/payment.py\n"
                "@@ -12,6 +12,9 @@\n+    async with lock:\n"
                "+        if event_id in processed_events:\n+            return\n"
                "+        processed_events.add(event_id)\n     process_payment(event)\n"
            ),
        ),
        expect_prefilter_skip=False,
        expected_change_type="bugfix",
        expected_worthiness_min=30,
    ),
    EvalCase(
        name="trivial_css_tweak",
        context=CommitContext(
            repo_name="demo", commit_sha="a5", commit_message="style: adjust button padding",
            author="dev", changed_files=["src/styles/button.css"],
            diff=(
                "diff --git a/src/styles/button.css b/src/styles/button.css\n"
                "@@ -3,1 +3,1 @@\n-  padding: 8px;\n+  padding: 10px;"
            ),
        ),
        expect_prefilter_skip=False,
        expected_change_type="ui",
        expected_worthiness_max=30,
    ),
    EvalCase(
        name="meaningful_ui_overhaul",
        context=CommitContext(
            repo_name="demo", commit_sha="a6", commit_message="feat: redesign onboarding flow with progress stepper",
            author="dev", changed_files=["src/components/Onboarding.tsx", "src/components/Stepper.tsx"],
            diff=(
                "diff --git a/src/components/Stepper.tsx b/src/components/Stepper.tsx\n"
                "new file mode 100644\n--- /dev/null\n+++ b/src/components/Stepper.tsx\n"
                "@@ -0,0 +1,25 @@\n+export function Stepper({ steps, current }) {\n"
                "+  return (\n+    <div className='stepper'>\n"
                "+      {steps.map((s, i) => <Step key={i} active={i === current} label={s} />)}\n"
                "+    </div>\n+  );\n+}\n"
            ),
        ),
        expect_prefilter_skip=False,
        expected_change_type="ui",
        expected_worthiness_min=40,
    ),
    EvalCase(
        name="docs_only_trivial",
        context=CommitContext(
            repo_name="demo", commit_sha="a7", commit_message="docs: add missing param description",
            author="dev", changed_files=["docs/api.md"],
            diff="diff --git a/docs/api.md b/docs/api.md\n@@ -20,0 +21 @@\n+  @param timeout - request timeout in ms",
        ),
        expect_prefilter_skip=False,
        expected_change_type="docs",
        expected_worthiness_max=25,
    ),
    EvalCase(
        name="real_performance_win",
        context=CommitContext(
            repo_name="demo", commit_sha="a8",
            commit_message="perf: batch DB writes, cut sync job time from 40s to 6s",
            author="dev", changed_files=["src/jobs/sync.py"],
            diff=(
                "diff --git a/src/jobs/sync.py b/src/jobs/sync.py\n@@ -8,7 +8,9 @@\n"
                "-    for record in records:\n-        db.save(record)\n"
                "+    with db.batch() as batch:\n+        for record in records:\n"
                "+            batch.add(record)\n"
            ),
        ),
        expect_prefilter_skip=False,
        expected_change_type="performance",
        expected_worthiness_min=50,
    ),
]