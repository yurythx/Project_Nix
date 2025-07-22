from .orchestrator import SetupWizardOrchestrator
from .steps.database import DatabaseStepHandler
from .steps.admin import AdminStepHandler
from .steps.email import EmailStepHandler
from .steps.security import SecurityStepHandler
from .steps.finalize import FinalizeStepHandler

wizard_steps = {
    'database': DatabaseStepHandler(),
    'admin': AdminStepHandler(),
    'email': EmailStepHandler(),
    'security': SecurityStepHandler(),
    'finalize': FinalizeStepHandler(),
}

orchestrator = SetupWizardOrchestrator(wizard_steps) 