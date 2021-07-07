from uuid import uuid4

from prism_api.talktrack.entities import (
    TalkTrack,
    TalkTrackInfo,
    TalkTrackStatus,
    TalkTrackStep,
)

SESSION_ID = 'testuser'


mock_talktrack_info = TalkTrackInfo(
            talktrack_id='talktrack-123',
            title='test',
            steps=[TalkTrackStep(
                title='test',
                text='this is a test',
                order=1,
                workflow_name='process',
                actions=[],
            )]
        )

mock_talktrack = TalkTrack(
    id=uuid4(),
    session_id=SESSION_ID,
    order=1,
    details=mock_talktrack_info,
    status=TalkTrackStatus.ACTIVE,
)
