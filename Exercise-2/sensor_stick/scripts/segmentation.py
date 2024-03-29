#!/usr/bin/env python

# Import modules
from pcl_helper import *



# Callback function for your Point Cloud Subscriber
def pcl_callback(pcl_msg):

    #Convert ROS msg to PCL data
    cloud = ros_to_pcl(pcl_msg)

    #  Voxel Grid Downsampling
    vox = cloud.make_voxel_grid_filter()
    LEAF_SIZE = 0.01
    vox.set_leaf_size(LEAF_SIZE, LEAF_SIZE, LEAF_SIZE)
    cloud_filtered = vox.filter()

    # PassThrough Filter
    passthrough = cloud_filtered.make_passthrough_filter()
    filter_axis = 'z'
    passthrough.set_filter_field_name(filter_axis)
    axis_min = 0.75
    axis_max = 1.3
    passthrough.set_filter_limits(axis_min, axis_max)
    cloud_filtered = passthrough.filter()


    # RANSAC Plane Segmentation
    plane_seg = cloud_filtered.make_segmenter()
    plane_seg.set_model_type(pcl.SACMODEL_PLANE)
    plane_seg.set_method_type(pcl.SAC_RANSAC)
    max_distance = 0.02
    plane_seg.set_distance_threshold(max_distance)
    inliers, coefficients = plane_seg.segment()

    # Extract inliers and outliers
    cloud_table   = cloud_filtered.extract(inliers, negative=False)
    cloud_objects = cloud_filtered.extract(inliers, negative=True)
    ros_cloud_table = pcl_to_ros(cloud_table)
    ros_cloud_objects = pcl_to_ros(cloud_objects)

    # Euclidean Clustering
    #Euclidean clustering requires points with only spatial info.
    #Convert XYZRGB PC to XYZ then Construct K-d tree
    white_cloud = XYZRGB_to_XYZ(cloud_objects)
    tree = white_cloud.make_kdtree()
    ##Euclidean Clustering 
    # Create a cluster extraction object
    cluster_ex = white_cloud.make_EuclideanClusterExtraction()
    # Set tolerances for distance threshold 
    # as well as minimum and maximum cluster size (in points)
  
    cluster_ex.set_ClusterTolerance(0.05)
    cluster_ex.set_MinClusterSize(10)
    cluster_ex.set_MaxClusterSize(1000)
    # Search the k-d tree for clusters
    cluster_ex.set_SearchMethod(tree)
    # Extract indices for each of the discovered clusters
    #cluster_indices now contains a list of indices for each cluster (a list of lists)
    cluster_indices = cluster_ex.Extract()
    
    # Create Cluster-Mask Point Cloud to visualize each cluster separately
    #Assign a color corresponding to each segmented object in scene
    cluster_color = get_color_list(len(cluster_indices))

    color_cluster_point_list = []

    for j, indices in enumerate(cluster_indices):
    	for i, indice in enumerate(indices):
    		color_cluster_point_list.append([white_cloud[indice][0],
                                             white_cloud[indice][1],
                                             white_cloud[indice][2],
                                             rgb_to_float(cluster_color[j])])



    #Create Cluster-Mask Point Cloud to visualize each cluster separately
    cluster_cloud = pcl.PointCloud_PointXYZRGB()
    cluster_cloud.from_list(color_cluster_point_list)

    # Convert PCL data to ROS messages
    ros_cluster_cloud = pcl_to_ros(cluster_cloud)

    #Publish ROS messages
    pcl_objects_pub.publish(ros_cloud_objects)
    pcl_table_pub.publish(ros_cloud_table)
    pcl_cluster_pub.publish(ros_cluster_cloud)


if __name__ == '__main__':

    # ROS node initialization
    rospy.init_node('clustering', anonymous=True)

    # Create Subscribers
    pcl_sub = rospy.Subscriber("/sensor_stick/point_cloud", pc2.PointCloud2, pcl_callback, queue_size=1)


    # Create Publishers
    pcl_objects_pub = rospy.Publisher("/pcl_objects", PointCloud2, queue_size=1)
    pcl_table_pub   = rospy.Publisher("/pcl_table"  , PointCloud2, queue_size=1)
    pcl_cluster_pub = rospy.Publisher("/pcl_cluster", PointCloud2, queue_size=1)

    # Initialize color_list
    get_color_list.color_list = []

    # Spin while node is not shutdown
    while not rospy.is_shutdown():
    	 rospy.spin()


