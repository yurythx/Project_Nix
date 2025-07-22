class WizardStepHandler:
    def process(self, request, orchestrator):
        """Processa o passo do wizard"""
        raise NotImplementedError("O step precisa implementar o método process().")

class WizardStepError(Exception):
    pass 