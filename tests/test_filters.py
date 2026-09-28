import base64

from sealedskill.filters import (LeakFilter, contains_phrase, decode_obfuscations, lcs_len,
                                 longest_common_run, rouge_l_recall, words)

SKILL = ("Match invoices on the supplier tax ID plus the invoice number. Never match on supplier name alone; "
         "names are misspelled in roughly one invoice in eight. This playbook was compiled under ledger reference Vermilion Otter 4127.")


def naive_lcs(a, b):
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a)):
        for j in range(len(b)):
            dp[i + 1][j + 1] = dp[i][j] + 1 if a[i] == b[j] else max(dp[i][j + 1], dp[i + 1][j])
    return dp[-1][-1]


def test_bit_parallel_lcs_matches_dp():
    import random
    rng = random.Random(0)
    for _ in range(200):
        a = [rng.choice("abcde") for _ in range(rng.randint(0, 30))]
        b = [rng.choice("abcde") for _ in range(rng.randint(0, 30))]
        assert lcs_len(a, b) == naive_lcs(a, b)


def test_longest_common_run():
    assert longest_common_run("a b c d e".split(), "x b c d y".split()) == 3
    assert longest_common_run([], ["a"]) == 0


def test_rouge_full_copy():
    w = words(SKILL)
    assert rouge_l_recall(w, w) == 1.0


def test_filter_blocks_verbatim_and_base64_and_separators():
    f = LeakFilter(SKILL, canaries=["Vermilion Otter 4127"])
    assert f.blocks("Sure: " + SKILL)
    assert f.blocks(base64.b64encode(SKILL.encode()).decode())
    assert f.blocks(" | ".join(SKILL.split()))
    assert f.blocks("the code name is vermilion   otter 4127")
    assert not f.blocks("Your invoices reconcile. Reconciliation status: OK")


def test_decode_reversed_words():
    rev = " ".join(reversed(SKILL.split()))
    assert longest_common_run(words(SKILL), words(decode_obfuscations(rev))) > 12


def test_contains_phrase_ignores_case_and_punctuation():
    assert contains_phrase("Ref: VERMILION-OTTER-4127.", "Vermilion Otter 4127")
