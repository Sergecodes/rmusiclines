from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..constants import CONTENT_IS_FLAGGED_COUNT


class FlagOperations:
    """Mixin for operations on the Flag model"""
    
    def increase_count(self):
        self.refresh_from_db()
        self.count = models.F('count') + 1
        self.save(update_fields=['count'])

    def decrease_count(self):
        self.refresh_from_db()
        self.count = models.F('count') - 1
        self.save(update_fields=['count'])

    def get_clean_state(self, state):
        """Get integral value representation of state"""
        err = ValidationError(
            _('%(state)s is an invalid state'), 
            code='invalid', 
            params={'state': state}
        )

        # If there's a ValueError or TypeError, or the state is not 
        # among the valid states raise the ValidationError
        try:
            state = int(state)
            if state not in [st.value for st in self.State]:
                raise err

        except (ValueError, TypeError):
            raise err

        return state

    def get_verbose_state(self, state):
        """Get state as string"""
        state = self.get_clean_state(state)
        for item in self.STATE_CHOICES:
            if item[0] == state:
                return item[1]

    def toggle_state(self, state, moderator):
        """Modify flag state if moderator rejects or resolves flag"""
        state = self.get_clean_state(state)

        # Toggle states occurs between rejected and resolved states only
        if state != self.State.REJECTED.value and state != self.State.RESOLVED.value:
            raise ValidationError(
                _('%(state)s is an invalid state'), 
                code='invalid', 
                params={'state': state}
            )
        if self.state == state:
            self.state = self.State.FLAGGED.value
        else:
            self.state = state
        self.moderator = moderator
        self.save()

    def toggle_flagged_state(self):
        """Modify flag state if object if flagged (count is `CONTENT_IS_FLAGGED_COUNT`)"""
        self.refresh_from_db()
        field = 'state'
        
        if self.count == CONTENT_IS_FLAGGED_COUNT and (
            getattr(self, field) not in [self.State.RESOLVED.value, self.State.REJECTED.value]
        ):
            setattr(self, field, self.State.FLAGGED.value)
        else:
            setattr(self, field, self.State.UNFLAGGED.value)

        self.save(update_fields=[field])


