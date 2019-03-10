import pytest

from marvin.responses import karma_regex


@pytest.mark.parametrize("vote", ["++", "--"])
def test_regex_works_with_reason(vote):
    match = karma_regex.match(f"dylan{vote} for this PR")
    assert match.groups() == ("dylan", vote, " for this PR")


@pytest.mark.parametrize("vote", ["++", "--"])
def test_regex_works_without_reason(vote):
    match = karma_regex.match(f"dylan{vote}")
    assert match.groups() == ("dylan", vote, "")


@pytest.mark.parametrize("vote", ["++", "--"])
def test_regex_works_with_whitespace_subject(vote):
    match = karma_regex.match(f"chris and dylan{vote} for this PR")
    assert match.groups() == ("chris and dylan", vote, " for this PR")


@pytest.mark.parametrize("vote", ["++", "--"])
def test_regex_ignores_if_vote_is_preceded_by_space(vote):
    match = karma_regex.match(f"hey you guys {vote}> I saw this thing")
    assert match is None


@pytest.mark.parametrize("vote", ["++", "--"])
def test_regex_ignores_if_vote_is_followed_by_nonspace(vote):
    match = karma_regex.match(f"hey you guys{vote}> I saw this thing")
    assert match is None
