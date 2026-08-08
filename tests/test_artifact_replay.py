from scripts.replay_artifacts import replay_second_family, replay_tool_call


def test_second_family_scores_and_summary_replay_exactly() -> None:
    result = replay_second_family()
    assert result["replayed_rows"] == 398
    assert result["row_score_mismatches"] == []
    assert result["paired_summary_mismatches"] == []
    assert result["valid"] is True


def test_tool_call_scores_and_summary_replay_exactly() -> None:
    result = replay_tool_call()
    assert result["replayed_rows"] == 66
    assert result["row_score_mismatches"] == []
    assert result["paired_summary_mismatches"] == []
    assert result["valid"] is True
