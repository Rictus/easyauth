import pytest


@pytest.mark.asyncio
async def test_server_authentication(auth_test_server):
    test_client = auth_test_server
    prefix = test_client.app.auth.ADMIN_PREFIX
    server = test_client.app

    # verify endpoint access fails without token

    response = test_client.get("/finance/")
    assert response.status_code == 401, f"{response.text} - {response.status_code}"

    # verify token generation with bad credentials

    bad_credentials = {"username": "admin", "password": "BAD"}

    response = test_client.post("/auth/token/login", json=bad_credentials)
    assert response.status_code == 401, f"{response.text} - {response.status_code}"

    # verify token generation with correct credentials

    good_credentials = {"username": "admin", "password": "easyauth"}

    response = test_client.post("/auth/token/login", json=good_credentials)
    assert response.status_code == 200, f"{response.text} - {response.status_code}"

    token = response.json()
    for expected in {"access_token", "token_type"}:
        assert "access_token" in token, f"missing {expected} in token {token}"

    # verify endpoint access while using token

    headers = {"Authorization": f"Bearer {token['access_token']}"}

    response = test_client.get("/finance/", headers=headers)
    assert response.status_code == 200, f"{response.text} - {response.status_code}"

    # test user creation
    new_user = {
        "username": "john",
        "password": "abcd1234",
        "full_name": "john doe",
        "email": "john.doe@easyauth.com",
        "groups": ["administrators"],
    }

    # check if user exists, delete if existing
    response = test_client.get("/auth/users/john", headers=headers)
    assert response.status_code in {
        200,
        404,
    }, f"{response.text} - {response.status_code}"
    if response.status_code == 200:
        # delete user
        response = test_client.delete("/auth/user?username=john", headers=headers)
        assert response.status_code == 200, f"{response.text} - {response.status_code}"

    # create user

    response = test_client.put("/auth/user", headers=headers, json=new_user)
    assert response.status_code == 201, f"{response.text} - {response.status_code}"

    # test updating user
    response = test_client.post(
        "/auth/user/john",
        headers=headers,
        json={"full_name": "john j doe", "password": "new1234"},
    )

    assert response.status_code == 200, f"{response.text} - {response.status_code}"

    # test deleting user
    response = test_client.delete("/auth/user?username=john", headers=headers)
    assert response.status_code == 200, f"{response.text} - {response.status_code}"

    # re-create & test token login with new user

    response = test_client.put("/auth/user", headers=headers, json=new_user)
    assert response.status_code == 201, f"{response.text} - {response.status_code}"

    response = test_client.post(
        "/auth/token/login",
        json={"username": new_user["username"], "password": new_user["password"]},
    )
    assert response.status_code == 200, f"{response.text} - {response.status_code}"

    token = response.json()
    headers = {"Authorization": f"Bearer {token['access_token']}"}

    response = test_client.get("/finance/", headers=headers)
    assert response.status_code == 200, f"{response.text} - {response.status_code}"

    # test permission creation

    # check if action exists, delete if existing
    response = test_client.get("/auth/actions/BASIC_CREATE", headers=headers)
    assert response.status_code in {
        200,
        404,
    }, f"{response.text} - {response.status_code}"
    if response.status_code == 200:
        # delete user
        response = test_client.delete(
            "/auth/action?action=BASIC_CREATE", headers=headers
        )
        assert response.status_code == 200, f"{response.text} - {response.status_code}"

    new_action = {"action": "BASIC_CREATE", "details": "BASIC CREATE action"}
    response = test_client.put("/auth/actions", headers=headers, json=new_action)
    assert response.status_code == 201, f"{response.text} - {response.status_code}"

    # test updating permission
    response = test_client.post(
        "/auth/actions?action=BASIC_CREATE",
        headers=headers,
        json={"details": "BASIC CREATE updated"},
    )

    assert response.status_code == 200, f"{response.text} - {response.status_code}"

    # test role creation

    # check if role exists, delete if existing
    response = test_client.get("/auth/roles/basic", headers=headers)
    assert response.status_code in {
        200,
        404,
    }, f"{response.text} - {response.status_code}"
    if response.status_code == 200:
        # delete role
        response = test_client.delete("/auth/role?role=basic", headers=headers)
        assert (
            response.status_code == 200
        ), f"delete role {response.text} - {response.status_code}"

    # create role

    new_role = {"role": "basic", "actions": ["BASIC_CREATE"]}

    response = test_client.put("/auth/role", headers=headers, json=new_role)
    assert (
        response.status_code == 201
    ), f"create role {response.text} - {response.status_code}"

    # test updating role
    response = test_client.post(
        "/auth/role/basic", headers=headers, json={"actions": ["BASIC_CREATE"]}
    )

    assert (
        response.status_code == 200
    ), f"update role {response.text} - {response.status_code}"

    # create group

    # check if group exists, delete if existing
    response = test_client.get("/auth/groups/basic_users", headers=headers)
    assert response.status_code in {
        200,
        404,
    }, f"get group{response.text} - {response.status_code}"
    if response.status_code == 200:
        # delete group
        response = test_client.delete(
            "/auth/group?group_name=basic_users", headers=headers
        )
        assert (
            response.status_code == 200
        ), f"delete group {response.text} - {response.status_code}"

    # create group

    new_group = {"group_name": "basic_users", "roles": ["basic"]}

    response = test_client.put("/auth/group", headers=headers, json=new_group)
    assert (
        response.status_code == 201
    ), f"create group {response.text} - {response.status_code}"

    # test updating role
    response = test_client.post(
        "/auth/group/basic_users", headers=headers, json={"roles": ["basic", "admin"]}
    )

    assert (
        response.status_code == 200
    ), f"update group {response.text} - {response.status_code}"

    # verify permission denied without required action
    response = test_client.get("/testing/actions", headers=headers)
    assert response.status_code == 403, f"{response.text} - {response.status_code}"

    # verify permission denied without required role
    response = test_client.get("/testing/roles", headers=headers)
    assert response.status_code == 403, f"{response.text} - {response.status_code}"

    # verify permission denied without required group
    response = test_client.get("/testing/groups", headers=headers)
    assert response.status_code == 403, f"{response.text} - {response.status_code}"

    # test get_user {'Authorization': 'Bearer tokenstr'}
    response = test_client.get("/testing/current_user", headers=headers)
    assert response.status_code == 200, f"{response.text} - {response.status_code}"
    assert "john" in response.text

    # test get_user - cookie only header
    token = headers["Authorization"].split(" ")[1]
    cookie_only = {"cookie": f"token={token}"}
    response = test_client.get("/testing/current_user", headers=cookie_only)
    assert response.status_code == 200, f"{response.text} - {response.status_code}"
    assert "john" in response.text

    # verify permission allowed for specific user
    response = test_client.get("/testing/", headers=headers)
    assert response.status_code == 200, f"{response.text} - {response.status_code}"

    # add user to group with

    response = test_client.post(
        "/auth/user/john", headers=headers, json={"groups": ["basic_users"]}
    )

    # verify failures pre token generation

    response = test_client.get("/testing/actions", headers=headers)
    assert response.status_code == 403, f"{response.text} - {response.status_code}"

    # verify permission denied without required action
    response = test_client.get("/testing/roles", headers=headers)
    assert response.status_code == 403, f"{response.text} - {response.status_code}"

    # verify permission denied without required action
    response = test_client.get("/testing/groups", headers=headers)
    assert response.status_code == 403, f"{response.text} - {response.status_code}"

    # re create token with updated permissions

    response = test_client.post(
        "/auth/token/login",
        json={"username": new_user["username"], "password": new_user["password"]},
    )
    assert response.status_code == 200, f"{response.text} - {response.status_code}"

    token = response.json()
    headers = {"Authorization": f"Bearer {token['access_token']}"}

    # verify success with updated token

    response = test_client.get("/testing/actions", headers=headers)
    assert (
        response.status_code == 200
    ), f"new_token - actions {response.text} - {response.status_code}"

    # verify permission denied without required action
    response = test_client.get("/testing/roles", headers=headers)
    assert (
        response.status_code == 200
    ), f"new_token - roles {response.text} - {response.status_code}"

    # verify permission denied without required action
    response = test_client.get("/testing/groups", headers=headers)
    assert (
        response.status_code == 200
    ), f"new_token - groups {response.text} - {response.status_code}"

    decoded_token = server.auth.decode_token(token["access_token"])
    print(decoded_token)
    assert "token_id" in decoded_token[1], f"{decoded_token}"

    # revoke token & test access failure
    response = test_client.delete(
        f"/auth/token?token_id={decoded_token[1]['token_id']}", headers=headers
    )
    assert (
        response.status_code == 200
    ), f"revoke token {response.text} - {response.status_code}"

    response = test_client.get("/testing/actions", headers=headers)
    assert (
        response.status_code == 403
    ), f"revoke_token - actions - {response.status_code} - {response.text}"

    response = test_client.get("/testing/roles", headers=headers)
    assert (
        response.status_code == 403
    ), f"revoke_token - roles {response.status_code} - {response.text}"

    response = test_client.get("/testing/groups", headers=headers)
    assert (
        response.status_code == 403
    ), f"revoke_token - groups - {response.status_code} - {response.text}"
