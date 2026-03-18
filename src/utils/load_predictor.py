class LoadPredictor:
    """Predicts system load using moving average."""
    
    def __init__(self, window=5):
        self.window = window
        self.history = []
    
    def moving_average(self, history=None):
        """Calculate moving average of queue lengths."""
        if history is None:
            history = self.history
        
        if len(history) < self.window:
            return sum(history) / len(history) if history else 0
        
        return sum(history[-self.window:]) / self.window
    
    def add_measurement(self, queue_length):
        """Add new queue length measurement."""
        self.history.append(queue_length)
    
    def predict(self):
        """Get predicted load (moving average)."""
        return self.moving_average()
    
    def is_overloaded(self, threshold):
        """Check if predicted load exceeds threshold."""
        return self.predict() > threshold
