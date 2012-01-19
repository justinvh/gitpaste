def has_access_to_paste(paste_set, request, private_key=None):
    """ Check whether a user has access to a paste based on the request """
    if paste_set.private and (request.user.id is None or request.user.pk != paste_set.owner.pk):
        if private_key != paste_set.private_key:
            return False
    return True