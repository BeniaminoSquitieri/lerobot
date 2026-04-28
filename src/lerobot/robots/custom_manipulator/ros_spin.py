from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.task import Future


def spin_until_future_complete(node: Node, future: Future) -> None:
    """Wait for a future without reusing rclpy's already-spinning global executor."""
    executor = SingleThreadedExecutor(context=node.context)
    added = executor.add_node(node)
    try:
        executor.spin_until_future_complete(future)
    finally:
        if added:
            executor.remove_node(node)
        executor.shutdown()
