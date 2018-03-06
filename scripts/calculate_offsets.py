#!/usr/bin/env python

from subprocess import call

import rospy
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from force_torque_sensor.srv import CalculateSensorOffset
from geometry_msgs.msg import Wrench

def calculate_sensor_offsets():
    
    rospy.init_node('calculate_offsets')
    
    package_to_store = rospy.get_param('~package_to_store')
    store_to_file = rospy.get_param('~store_to_file')
    robot = rospy.get_param('~robot')
    if robot == "kuka":
        joint_names = rospy.get_param('/controller_joint_names')
        controller_topic = '/position_trajectory_controller/command'
        calcOffset_service = '/CalculateOffsets'
    else:
        joint_names = rospy.get_param('/arm/joint_names')
        controller_topic = '/arm/joint_trajectory_controller/command'
        calcOffset_service = '/arm/CalculateOffsets'

    trajectory_pub = rospy.Publisher(controller_topic, JointTrajectory, latch=True, queue_size=1)
    calculate_offsets_srv = rospy.ServiceProxy(calcOffset_service, CalculateSensorOffset)
    
    ##print call('rospack find force_torque_sensor', shell=True)
    ##call('rosparam dump -v `rospack find force_torque_sensor`/config/sensor_offset.yaml /fts/Offset')
    
    # Posees
    poses = [[0.0, 0.0, 1.5707963, 0.0, -1.5707963, 0.0],
             [0.0, 0.0, 1.5707963, 0.0, 1.5707963, 0.0]]

    poses_kuka = [[0.0, -1.5707963, 1.5707963, 0.0, -1.5707963, 0.0],
             [0.0, -1.5707963, 1.5707963, 0.0, 1.5707963, 0.0]]

    measurement = Wrench()
    
    for i in range(0,len(poses)):
        trajectory = JointTrajectory()
        point = JointTrajectoryPoint()
        trajectory.header.stamp = rospy.Time.now()
        trajectory.joint_names = joint_names
        
        point.time_from_start = rospy.Duration(2.5)
        if robot == "kuka":
            point.positions = poses_kuka[i]
        else:
            point.positions = poses[i]
        
        trajectory.points.append(point)        
        trajectory_pub.publish(trajectory)            
        rospy.loginfo("Going to position: " + str(point.positions))
                
        rospy.sleep(10.0)
        
        rospy.loginfo("Calculating offsets.")
        ret = calculate_offsets_srv(False)

        measurement.force.x += ret.offset.force.x
        measurement.force.y += ret.offset.force.y
        measurement.force.z += ret.offset.force.z
        measurement.torque.x += ret.offset.torque.x
        measurement.torque.y += ret.offset.torque.y
        measurement.torque.z += ret.offset.torque.z

    measurement.force.x /= len(poses)
    measurement.force.y /= len(poses)
    measurement.force.z /= len(poses)
    measurement.torque.x /= len(poses)
    measurement.torque.y /= len(poses)
    measurement.torque.z /= len(poses)

    rospy.set_param('/temp/Offset/force/x', measurement.force.x)
    rospy.set_param('/temp/Offset/force/y', measurement.force.y)
    rospy.set_param('/temp/Offset/force/z', measurement.force.z)
    rospy.set_param('/temp/Offset/torque/x', measurement.torque.x)
    rospy.set_param('/temp/Offset/torque/y', measurement.torque.y)
    rospy.set_param('/temp/Offset/torque/z', measurement.torque.z)    

    if store_to_file:
      call('rosparam dump -v `rospack find ' + package_to_store + ' `/config/sensor_offset.yaml /temp/Offset', shell=True)


if __name__ == "__main__":
    
    try:
        calculate_sensor_offsets()
    except rospy.ROSInterruptException:
        pass
