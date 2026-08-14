from evals.dataset import CASES, EvalCase
from social_agent.guardrails.prefilter import should_skip
from social_agent.nodes.classify import classify_and_score


def _check_case(case: EvalCase) -> tuple[bool, list[str]]:
    failures = []

    skip, reason = should_skip(case.context)
    if skip != case.expect_prefilter_skip:
        failures.append(f"prefilter: expected skip={case.expect_prefilter_skip}, got {skip} ({reason})")

    if skip:
        return not failures, failures

    classification, worthiness = classify_and_score(case.context)

    if case.expected_change_type and classification.change_type != case.expected_change_type:
        failures.append(f"change_type: expected {case.expected_change_type}, got {classification.change_type}")

    if case.expected_worthiness_min is not None and worthiness.score < case.expected_worthiness_min:
        failures.append(f"worthiness: expected >= {case.expected_worthiness_min}, got {worthiness.score}")

    if case.expected_worthiness_max is not None and worthiness.score > case.expected_worthiness_max:
        failures.append(f"worthiness: expected <= {case.expected_worthiness_max}, got {worthiness.score}")

    return not failures, failures


def main() -> None:
    passed = 0
    for case in CASES:
        ok, failures = _check_case(case)
        print(f"[{'PASS' if ok else 'FAIL'}] {case.name}")
        for failure in failures:
            print(f"       - {failure}")
        passed += ok

    print(f"\n{passed}/{len(CASES)} passed")


if __name__ == "__main__":
    main()