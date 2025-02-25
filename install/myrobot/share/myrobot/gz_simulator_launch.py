import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, IncludeLaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    bringup_dir = Path(get_package_share_directory('myrobot'))

    world = bringup_dir / "world" / "depot.sdf"
    sdf_file = bringup_dir / 'urdf' / 'robot.sdf'

    with open(sdf_file, 'r') as infp:
        robot_desc = infp.read()

    start_robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='both',
        parameters=[{'use_sim_time': use_sim_time}, {'robot_description': robot_desc}]
    )

    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=f"{bringup_dir / 'world'}:{bringup_dir.parent.resolve()}"
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': str(bringup_dir / 'config' / 'gz_bridge.yaml'),
            'qos_overrides./tf_static.publisher.durability': 'transient_local',
        }],
        output='screen'
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(Path(get_package_share_directory("ros_gz_sim")) / "launch" / "gz_sim.launch.py")),
        launch_arguments={'gz_args': f"-r -v 4 {world}"}.items(),
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "robot",
            "-file", str(sdf_file),
            "-x", "0", "-y", "0", "-z", "2.0",
        ],
        output="screen",
    )

    tf_map = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=["0", "0", "0", "0", "0", "0", "map", "odom"]
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='True', description='Use sim time if true'),
        DeclareLaunchArgument('urdf_file', default_value=str(bringup_dir / 'urdf' / 'assembly_robot.urdf'), description='URDF file path'),
        gz_resource_path,
        gz_sim, bridge, spawn_entity, start_robot_state_publisher_cmd, tf_map, joint_state_publisher
    ])

