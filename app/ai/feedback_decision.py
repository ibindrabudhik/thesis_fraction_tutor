def choose_feedback_type(spk, sal, tof):
    """
    Modify feedback type based on SPK (student prior knowledge) and SAL (student achievement level) profiles.
    """

    if spk == "Low" and sal == "Low":
        return "Response Contingent"
    elif spk == "High" and sal == "Low":
        return "Topic Contingent"
    elif spk == "Low" and sal == "High" and tof == "Immediate":
        return "Response Contingent"
    elif spk == "High" and sal == "High" and tof == "Immediate":
        return "Try again + Delayed Topic Content"
    elif spk == "Low" and sal == "High" and tof == "Delayed":
        return "Verification + Response Contingent"
    elif spk == "High" and sal == "High" and tof == "Delayed":
        return "Try again + Delayed Topic Contingent"
    else:
        return "Standard Feedback"
    