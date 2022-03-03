import logging
from datetime import datetime

from peewee import *


database = SqliteDatabase('data.db',pragmas={'foreign_keys': 1})

logger = logging.getLogger('nym')

def create_tables():
    with database:
        database.create_tables([User, Mixnode,Gateway])


class BaseModel(Model):
    class Meta:
        database = database

    def connect(self):
        logHandler = logging.getLogger('nym')

        try:
            database.connect()
        except Exception as e:
            logHandler.exception(e)

    def close(self):
        logHandler = logging.getLogger('nym')

        try:
            database.close()
        except Exception as e:
            logHandler.exception(e)

    def insertUser(self, userid, mixnodeid=None,state=True,gatewayid=None):
        logHandler = logging.getLogger('nym')
        logHandler.debug(mixnodeid)
        self.connect()

        try:
            with database.atomic():
                if mixnodeid is not None:
                    mixnodeFk = Mixnode.get(Mixnode.identityKey == mixnodeid)
                    lenghtUser = User.select(User.userid, User.state).where(
                        (User.userid == userid) & (User.mixnodeid == mixnodeFk)).count()
                elif gatewayid is not None:
                    gwFk = Gateway.get(Gateway.identityKey == gatewayid)
                    lenghtUser = User.select(User.userid, User.state).where(
                        (User.userid == userid) & (User.gwid == gwFk)).count()

                if state:
                    if lenghtUser <= 0:
                        if mixnodeid is not None:
                            User.create(userid=userid, mixnodeid=mixnodeFk, state=state)
                            logHandler.info(f"New mixnode {mixnodeid}, userid {userid}")
                        elif gatewayid is not None:
                            User.create(userid=userid, gwid=gwFk, state=state)
                            logHandler.info(f"New gateway {gatewayid}, userid {userid}")
                        return True
                    else:
                        if mixnodeid is not None:
                            logHandler.error(f"Already exists {mixnodeid}, userid {userid}")
                        elif gatewayid is not None:
                            logHandler.error(f"Already exists {gatewayid}, userid {userid}")
                        return False
                else:
                    if lenghtUser >= 1:
                        if mixnodeid is not None:
                            User.delete().where((User.userid == userid) & (User.mixnodeid == mixnodeFk)).execute()
                            logHandler.info(f"Delete mixnode {mixnodeid}, userid {userid}")
                        elif gatewayid is not None:
                            User.delete().where((User.userid == userid) & (User.gwid == gwFk)).execute()
                            logHandler.info(f"Delete gw {gatewayid}, userid {userid}")
                        return True
                    else:
                        if mixnodeid is not None:
                            logHandler.error(f"Delete Mixnode {mixnodeid}, userid {userid}")
                        elif gatewayid is not None:
                            logHandler.error(f"Delete gw {gatewayid}, userid {userid}")

                        return False
        except IntegrityError as e:
            print(e)
            logHandler.exception(e)
            return False
        except DoesNotExist as e:
            logHandler.exception(e)
            return False
        finally:
            self.close()

    def deleteNode(self, identityKey, isGw=False):
        logHandler = logging.getLogger('nym')
        self.connect()
        print(isGw)
        if not isGw:
            mixnodeFk = Mixnode.get(Mixnode.identityKey == identityKey)

            logHandler.debug(f"Delete mixnode {identityKey}")
            User.delete().where(User.mixnodeid == mixnodeFk).execute()
            #Mixnode.delete().where(Mixnode.id == mixnodeFk).execute()
        else:
            gatewayFk = Gateway.get(Gateway.identityKey == identityKey)

            logHandler.debug(f"Delete gw {identityKey}")
            User.delete().where(User.gwid == gatewayFk).execute()
            #Gateway.delete().where(Gateway.id == gatewayFk).execute()

        self.close()


    def insertMixnode(self, identityKey, status):
        logHandler = logging.getLogger('nym')
        self.connect()

        try:
            with database.atomic():
                Mixnode.insert(identityKey=identityKey, status=status).on_conflict(
                    conflict_target=[Mixnode.identityKey],
                    update={Mixnode.status: status,Mixnode.updated_on: datetime.now()}).execute()
        except IntegrityError as e:
            logHandler.exception(e)
        finally:
            self.close()

    def insertGw(self, identityKey, count):
        logHandler = logging.getLogger('nym')
        self.connect()

        try:
            with database.atomic():
                Gateway.insert(identityKey=identityKey, counter=count).on_conflict(
                    conflict_target=[Gateway.identityKey],
                    update={Gateway.counter: count,Gateway.updated_on: datetime.now()}).execute()
        except IntegrityError as e:
            logHandler.exception(e)
        finally:
            self.close()

    def updateStatus(self, identityKey, status):
        logHandler = logging.getLogger('nym')
        self.connect()

        try:
            with database.atomic():
                Mixnode.update(state=status).where(Mixnode.identityKey == identityKey).execute()
            return True
        except IntegrityError as e:
            print(e)
            logHandler.exception(e)
            return False
        finally:
            self.close()

    def updateCounter(self, identityKey, count):
        logHandler = logging.getLogger('nym')
        self.connect()

        try:
            with database.atomic():
                Gateway.update(counter=count).where(Gateway.identityKey == identityKey).execute()
            return True
        except IntegrityError as e:
            print(e)
            logHandler.exception(e)
            return False
        finally:
            self.close()

    def getMixnodes(self):
        self.connect()
        data = [mixnode for mixnode in Mixnode.select(Mixnode.identityKey,Mixnode.status).dicts()]
        self.close()
        return data

    def getMixnodesUser(self,identityKey):
        self.connect()
        mixnodeFk = Mixnode.get(Mixnode.identityKey == identityKey)
        data = [userid for userid in User.select(User.userid,User.state).where((User.mixnodeid == mixnodeFk) & (User.state == True)).dicts()]
        self.close()
        return data

    def getGw(self):
        self.connect()
        data = [gw for gw in Gateway.select(Gateway.identityKey,Gateway.counter).dicts()]
        self.close()
        return data

    def getGwUser(self,identityKey):
        self.connect()
        gwFk = Gateway.get(Gateway.identityKey == identityKey)
        data = [userid for userid in User.select(User.userid,User.state).where((User.gwid == gwFk) & (User.state == True)).dicts()]
        self.close()
        return data

class Gateway(BaseModel):
    identityKey = CharField(unique=True)
    counter = BigIntegerField()

    created_on = DateTimeField(default=datetime.now)
    updated_on = DateTimeField(default=datetime.now)


class Mixnode(BaseModel):
    identityKey = CharField(unique=True)
    status = CharField()

    created_on = DateTimeField(default=datetime.now)
    updated_on = DateTimeField(default=datetime.now)


class User(BaseModel):
    userid = CharField()
    mixnodeid = ForeignKeyField(Mixnode, backref='user',null=True)
    gwid = ForeignKeyField(Gateway, backref='user',null=True)
    state = BooleanField()

    created_on = DateTimeField(default=datetime.now)
    updated_on = DateTimeField(default=datetime.now)


