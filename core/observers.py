"""
Observer Pattern Implementation
Provides event-driven communication between components
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event data structure"""
    name: str
    data: Any
    timestamp: datetime
    source: str
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class IObserver(ABC):
    """Observer interface"""
    
    @abstractmethod
    def update(self, event: Event) -> None:
        """Handle event update"""
        pass


class IEventDispatcher(ABC):
    """Event dispatcher interface"""
    
    @abstractmethod
    def subscribe(self, event_name: str, observer: IObserver) -> None:
        """Subscribe observer to event"""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_name: str, observer: IObserver) -> None:
        """Unsubscribe observer from event"""
        pass
    
    @abstractmethod
    def dispatch(self, event: Event) -> None:
        """Dispatch event to all subscribers"""
        pass


class EventDispatcher(IEventDispatcher):
    """Event dispatcher implementation"""
    
    def __init__(self):
        self._subscribers: Dict[str, Set[IObserver]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_name: str, observer: IObserver) -> None:
        """Subscribe observer to event"""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = set()
        self._subscribers[event_name].add(observer)
        logger.info(f"Observer {type(observer).__name__} subscribed to {event_name}")
    
    def unsubscribe(self, event_name: str, observer: IObserver) -> None:
        """Unsubscribe observer from event"""
        if event_name in self._subscribers:
            self._subscribers[event_name].discard(observer)
            if not self._subscribers[event_name]:
                del self._subscribers[event_name]
            logger.info(f"Observer {type(observer).__name__} unsubscribed from {event_name}")
    
    def dispatch(self, event: Event) -> None:
        """Dispatch event to all subscribers"""
        try:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            # Notify subscribers
            if event.name in self._subscribers:
                for observer in self._subscribers[event.name].copy():
                    try:
                        observer.update(event)
                    except Exception as e:
                        logger.error(f"Error in observer {type(observer).__name__}: {e}")
                        logger.debug(traceback.format_exc())
            
            logger.debug(f"Event {event.name} dispatched to {len(self._subscribers.get(event.name, set()))} observers")
            
        except Exception as e:
            logger.error(f"Error dispatching event {event.name}: {e}")
            logger.debug(traceback.format_exc())
    
    def get_subscribers_count(self, event_name: str) -> int:
        """Get number of subscribers for an event"""
        return len(self._subscribers.get(event_name, set()))
    
    def get_event_history(self, event_name: Optional[str] = None) -> List[Event]:
        """Get event history, optionally filtered by event name"""
        if event_name:
            return [event for event in self._event_history if event.name == event_name]
        return self._event_history.copy()


class CallbackObserver(IObserver):
    """Observer that uses a callback function"""
    
    def __init__(self, callback: Callable[[Event], None]):
        self.callback = callback
    
    def update(self, event: Event) -> None:
        """Call the callback function"""
        self.callback(event)


class LoggingObserver(IObserver):
    """Observer that logs events"""
    
    def __init__(self, log_level: int = logging.INFO):
        self.log_level = log_level
    
    def update(self, event: Event) -> None:
        """Log the event"""
        logger.log(self.log_level, f"Event: {event.name} from {event.source} at {event.timestamp}")


class MetricsObserver(IObserver):
    """Observer that collects metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, int] = {}
    
    def update(self, event: Event) -> None:
        """Update metrics"""
        if event.name not in self.metrics:
            self.metrics[event.name] = 0
        self.metrics[event.name] += 1
    
    def get_metrics(self) -> Dict[str, int]:
        """Get collected metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset metrics"""
        self.metrics.clear()


# Global event dispatcher instance
event_dispatcher = EventDispatcher()


def dispatch_event(name: str, data: Any, source: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to dispatch events"""
    event = Event(name=name, data=data, timestamp=datetime.now(), source=source, metadata=metadata)
    event_dispatcher.dispatch(event)


def subscribe_to_event(event_name: str, observer: IObserver) -> None:
    """Convenience function to subscribe to events"""
    event_dispatcher.subscribe(event_name, observer)


def unsubscribe_from_event(event_name: str, observer: IObserver) -> None:
    """Convenience function to unsubscribe from events"""
    event_dispatcher.unsubscribe(event_name, observer)

# Exemplo de uso:
# from core.observers import event_dispatcher
# def on_article_created(article):
#     ...
# event_dispatcher.subscribe('article_created', on_article_created)
# event_dispatcher.notify('article_created', article) 