import os

from shared.utils import silence_warnings_and_logs

silence_warnings_and_logs()

import litellm  # noqa: E402 - must import after warning suppression
from agency_swarm import Agency  # noqa: E402 - must import after warning suppression
from dotenv import load_dotenv  # noqa: E402 - must import after warning suppression

from agency_code_agent.agency_code_agent import (  # noqa: E402 - must import after warning suppression
    create_agency_code_agent,
)

from qa_agent.qa_agent import (  # noqa: E402 - must import after warning suppression
    create_qa_agent,
)

from data_analyst_agent.data_analyst_agent import (  # noqa: E402 - must import after warning suppression
    create_data_analyst_agent,
)

from ad_creator_agent.ad_creator_agent import (  # noqa: E402 - must import after warning suppression
    create_ad_creator,
)

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
litellm.modify_params = True

model = "gpt-5"
coder = create_agency_code_agent(
    model=model, reasoning_effort="high"
)

qa = create_qa_agent(model=model, reasoning_effort="medium")

data_analyst = create_data_analyst_agent(model=model, reasoning_effort="medium")

ad_creator = create_ad_creator(model=model, reasoning_effort="medium")

def create_agency(load_threads_callback=None):
    agency = Agency(
        coder, data_analyst, ad_creator, qa,
        name="MultimodalAgency",
        communication_flows=[
            (coder, qa),
        ],
        load_threads_callback=load_threads_callback,
    )
    return agency

if __name__ == "__main__":
    agency = create_agency()
    agency.terminal_demo()
