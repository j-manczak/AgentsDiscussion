import streamlit as st
from pydantic import ValidationError

from debate.orchestrator import DebateOutcome
from debate.rounds import ROUND_NAMES
from debate.service import run_debate
from llm.client import ModelRequestError, ModelResponseError
from config.settings import ConfigurationError
from models.debate import DebateConfig
from players.lookup import PlayerLookupError, PlayerNotFoundError


st.set_page_config(page_title="Football Debate", page_icon="⚽", layout="wide")


def show_validation_error(error: ValidationError) -> None:
    messages = [item["msg"] for item in error.errors(include_input=False)]
    st.error("Please check your debate settings: " + " ".join(messages))


def render_argument(turn) -> None:
    st.markdown(f"**{turn.player_name} — {turn.agent_name}**")
    st.write(turn.argument.main_claim)
    if turn.argument.supporting_arguments:
        st.markdown("**Supporting arguments**")
        for argument in turn.argument.supporting_arguments:
            st.markdown(f"- {argument}")
    if turn.argument.rebuttals:
        st.markdown("**Responses to the opponent**")
        for rebuttal in turn.argument.rebuttals:
            st.markdown(f"- {rebuttal}")
    if turn.argument.concessions:
        st.markdown("**Points acknowledged**")
        for concession in turn.argument.concessions:
            st.markdown(f"- {concession}")
    if turn.argument.evidence:
        with st.expander("Evidence and uncertainty"):
            for evidence in turn.argument.evidence:
                status = "Verified" if evidence.is_verified else "Not independently verified"
                st.markdown(f"- **{evidence.claim}** ({evidence.confidence}; {status})")
                if evidence.source_name:
                    st.caption(evidence.source_name)
                if evidence.source_url:
                    st.markdown(f"[Source]({evidence.source_url})")
    st.write(turn.argument.conclusion)


def render_outcome(outcome: DebateOutcome) -> None:
    config = outcome.config
    verdict = outcome.verdict
    st.divider()
    st.header("Debate")
    for round_number in range(1, config.rounds + 1):
        st.subheader(f"Round {round_number}: {ROUND_NAMES[round_number]}")
        round_turns = [
            turn for turn in outcome.turns if turn.round_number == round_number
        ]
        left, right = st.columns(2)
        with left:
            render_argument(round_turns[0])
        with right:
            render_argument(round_turns[1])

    st.divider()
    st.header("Judge's verdict")
    if verdict.winner is None:
        st.subheader("Result: Draw")
    else:
        st.subheader(f"Winner: {verdict.winner}")
    score_a, score_b = st.columns(2)
    score_a.metric(config.player_a, f"{verdict.player_a_score:.2f} / 10")
    score_b.metric(config.player_b, f"{verdict.player_b_score:.2f} / 10")

    st.markdown("#### Scores by criterion")
    st.table(
        [
            {
                "Criterion": item.criterion_name,
                "Weight": f"{item.weight:.0%}",
                config.player_a: f"{item.player_a_score:.1f} / 10",
                config.player_b: f"{item.player_b_score:.1f} / 10",
                "Judge's reasoning": item.explanation,
            }
            for item in verdict.criteria_scores
        ]
    )
    st.markdown("#### Overall assessment")
    st.write(verdict.final_explanation)
    strong_a, strong_b = st.columns(2)
    with strong_a:
        st.markdown(f"#### Strongest arguments for {config.player_a}")
        for argument in verdict.strongest_arguments_a:
            st.markdown(f"- {argument}")
    with strong_b:
        st.markdown(f"#### Strongest arguments for {config.player_b}")
        for argument in verdict.strongest_arguments_b:
            st.markdown(f"- {argument}")
    if verdict.limitations:
        st.markdown("#### Limitations and uncertainty")
        for limitation in verdict.limitations:
            st.markdown(f"- {limitation}")
    st.caption(
        "This is an AI-generated assessment based on the stated criteria and debate. "
        "It is not objective truth; factual claims have not been independently verified."
    )


def main() -> None:
    st.title("⚽ Football Debate")
    st.write(
        "Two independent player advocates debate the comparison. A separate, "
        "neutral judge evaluates the completed transcript."
    )
    with st.form("debate_configuration"):
        col_a, col_b = st.columns(2)
        with col_a:
            player_a = st.text_input("First player", placeholder="Lionel Messi")
        with col_b:
            player_b = st.text_input("Second player", placeholder="Cristiano Ronaldo")
        rounds = st.radio(
            "Debate rounds",
            options=[1, 2, 3],
            index=2,
            horizontal=True,
            help="1: opening statements; 2: add counterarguments; 3: add final defense.",
        )
        context = st.text_area(
            "Optional context or comparison criteria",
            max_chars=2000,
            placeholder="For example: focus on peak performance and international tournaments.",
        )
        submitted = st.form_submit_button("Start debate", type="primary")

    if submitted:
        try:
            config = DebateConfig(
                player_a=player_a,
                player_b=player_b,
                rounds=rounds,
                additional_context=context,
            )
        except ValidationError as exc:
            show_validation_error(exc)
        else:
            st.session_state.pop("football_debate", None)
            try:
                with st.spinner("The agents are debating and the judge is evaluating..."):
                    st.session_state["football_debate"] = run_debate(config)
            except PlayerNotFoundError as exc:
                st.error(str(exc))
            except PlayerLookupError as exc:
                st.error(str(exc))
            except ConfigurationError as exc:
                st.error(str(exc))
            except ModelRequestError as exc:
                st.error(str(exc))
            except ModelResponseError as exc:
                st.error(
                    f"The debate could not be completed because an agent response was invalid. {exc}"
                )

    outcome = st.session_state.get("football_debate")
    if outcome is not None:
        render_outcome(outcome)


if __name__ == "__main__":
    main()
